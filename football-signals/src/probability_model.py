from __future__ import annotations

import re
from typing import Any

import numpy as np
from scipy.stats import poisson

from src.lineup_context import extract_missing, lambda_penalties
from src.season_strength import (
    TeamSeasonStats,
    estimate_lambdas_from_season,
    team_id_from_match,
)

# Максимальный счёт в матрице Пуассона
MAX_GOALS = 8

OUTCOME_LABELS = {
    "w1": "П1",
    "x": "X",
    "w2": "П2",
    "btts_yes": "ОЗ — да",
    "btts_no": "ОЗ — нет",
    "dc_1x": "1X",
    "dc_12": "12",
    "dc_x2": "X2",
    "total_over_25": "ТБ 2.5",
    "total_under_25": "ТМ 2.5",
    "dnb_1": "Фора 1 (0)",
    "dnb_2": "Фора 2 (0)",
}


def _parse_fraction(value: str | None) -> float | None:
    if not value:
        return None
    m = re.fullmatch(r"\s*(\d+)\s*/\s*(\d+)\s*", str(value))
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    if b <= 0:
        return None
    return a / b


def _streak_maps(pregame: dict) -> tuple[dict[str, float], dict[str, float]]:
    home: dict[str, float] = {}
    away: dict[str, float] = {}
    general = ((pregame.get("teamStreaks") or {}).get("general")) or []
    for item in general:
        name = str(item.get("name", "")).lower()
        team = item.get("team")
        frac = _parse_fraction(item.get("value"))
        raw_val = item.get("value")
        numeric = None
        if frac is not None:
            numeric = frac
        else:
            try:
                numeric = float(str(raw_val).replace(",", "."))
            except (TypeError, ValueError):
                numeric = None
        if numeric is None:
            continue
        target = home if team == "home" else away if team == "away" else None
        if target is None:
            continue
        target[name] = numeric
    return home, away


def _form_letters(form: Any, side: str) -> list[str]:
    """Достаёт W/D/L из form API (homeTeam/awayTeam + list или строка)."""
    if not form:
        return []
    raw: Any = None
    if isinstance(form, dict):
        block = (
            form.get(f"{side}Team")
            or form.get(side)
            or form.get(f"{side}Form")
            or form.get(f"{side}_form")
        )
        if isinstance(block, dict):
            raw = block.get("form") or block.get("string") or block.get("value")
        elif isinstance(block, (list, str)):
            raw = block
        elif side == "home" and isinstance(form.get("home"), (list, str)):
            raw = form.get("home")
        elif side == "away" and isinstance(form.get("away"), (list, str)):
            raw = form.get("away")
    elif isinstance(form, str) and side == "home":
        raw = form

    if isinstance(raw, list):
        return [str(x).upper() for x in raw if str(x).upper() in {"W", "D", "L"}][-5:]
    if isinstance(raw, str) and raw.strip():
        return [c.upper() for c in raw if c.upper() in {"W", "D", "L"}][-5:]
    return []


def _form_attack_shift(form: Any, side: str) -> float:
    letters = _form_letters(form, side)
    if not letters:
        return 0.0
    points = sum(3 if c == "W" else 1 if c == "D" else 0 for c in letters)
    avg = points / (3 * len(letters))  # 0..1
    return (avg - 0.5) * 0.35


def _estimate_lambdas(match: dict) -> tuple[float, float]:
    """
    λ из силы сезона (таблица), с поправками h2h / streaks / form.
    Коэффициенты букмекеров НЕ используются.
    """
    pregame = match.get("pregame") or {}
    by_team: dict[int, TeamSeasonStats] = match.get("_season_by_team") or {}
    season_pair = estimate_lambdas_from_season(
        team_id_from_match(match, "home"),
        team_id_from_match(match, "away"),
        by_team,
    )
    used_season = season_pair is not None
    if season_pair is not None:
        lambda_home, lambda_away = season_pair
    else:
        lambda_home = 1.35
        lambda_away = 1.10

    h2h = ((pregame.get("h2h") or {}).get("teamDuel")) or {}
    home_wins = float(h2h.get("homeWins") or 0)
    away_wins = float(h2h.get("awayWins") or 0)
    draws = float(h2h.get("draws") or 0)
    total = home_wins + away_wins + draws

    h2h_scale = 0.45 if used_season else 1.2
    if total >= 3:
        home_share = (home_wins + 0.5 * draws) / total
        lambda_home += (home_share - 0.5) * h2h_scale
        lambda_away += ((1.0 - home_share) - 0.5) * h2h_scale

    home_s, away_s = _streak_maps(pregame)
    streak_scale = 0.6 if used_season else 1.0

    def apply_over(streaks: dict[str, float], base: float) -> float:
        over = streaks.get("more than 2.5 goals")
        if over is not None:
            base += (over - 0.55) * 0.7 * streak_scale
        btts = streaks.get("both teams scoring")
        if btts is not None:
            base += (btts - 0.5) * 0.25 * streak_scale
        losses = streaks.get("losses")
        if losses is not None and losses >= 3:
            base -= 0.15 * streak_scale
        wins = streaks.get("wins")
        if wins is not None and wins >= 3:
            base += min(0.20, 0.05 * wins) * streak_scale
        no_losses = streaks.get("no losses")
        if no_losses is not None and no_losses >= 4:
            base += 0.08 * streak_scale
        first = streaks.get("first to score")
        if first is not None and first >= 0.7:
            base += 0.10 * streak_scale
        return base

    lambda_home = apply_over(home_s, lambda_home)
    lambda_away = apply_over(away_s, lambda_away)

    if away_s.get("without clean sheet", 0) >= 5:
        lambda_home += 0.15 * streak_scale
    if home_s.get("without clean sheet", 0) >= 5:
        lambda_away += 0.15 * streak_scale
    if home_s.get("no goals conceded", 0) >= 3:
        lambda_away -= 0.12 * streak_scale
    if away_s.get("no goals conceded", 0) >= 3:
        lambda_home -= 0.12 * streak_scale

    form = pregame.get("form")
    form_scale = 0.55 if used_season else 1.0
    lambda_home += _form_attack_shift(form, "home") * form_scale
    lambda_away += _form_attack_shift(form, "away") * form_scale

    miss_h, miss_a = lambda_penalties(extract_missing(match))
    lambda_home += miss_h
    lambda_away += miss_a

    lambda_home = float(np.clip(lambda_home, 0.35, 3.2))
    lambda_away = float(np.clip(lambda_away, 0.25, 3.0))
    return lambda_home, lambda_away


def _score_matrix(lambda_home: float, lambda_away: float, max_goals: int = MAX_GOALS) -> np.ndarray:
    home_probs = poisson.pmf(np.arange(0, max_goals + 1), lambda_home)
    away_probs = poisson.pmf(np.arange(0, max_goals + 1), lambda_away)
    matrix = np.outer(home_probs, away_probs)
    s = matrix.sum()
    if s <= 0:
        raise ValueError("degenerate poisson matrix")
    return matrix / s


def compute(match: dict) -> dict[str, float]:
    """
    Возвращает вероятности исходов независимо от oddsBk.
    Ключи совместимы со слагами API: w1/x/w2 + производные рынки.
    """
    lh, la = _estimate_lambdas(match)
    matrix = _score_matrix(lh, la)

    p_home = float(
        sum(matrix[i, j] for i in range(matrix.shape[0]) for j in range(matrix.shape[1]) if i > j)
    )
    p_draw = float(np.trace(matrix))
    p_away = float(
        sum(matrix[i, j] for i in range(matrix.shape[0]) for j in range(matrix.shape[1]) if i < j)
    )

    s = p_home + p_draw + p_away
    p_home, p_draw, p_away = p_home / s, p_draw / s, p_away / s

    p_btts_yes = float(
        sum(matrix[i, j] for i in range(1, matrix.shape[0]) for j in range(1, matrix.shape[1]))
    )
    p_btts_no = 1.0 - p_btts_yes

    p_over_25 = float(
        sum(
            matrix[i, j]
            for i in range(matrix.shape[0])
            for j in range(matrix.shape[1])
            if i + j >= 3
        )
    )
    p_under_25 = 1.0 - p_over_25

    denom = p_home + p_away
    if denom > 0:
        p_dnb_1 = p_home / denom
        p_dnb_2 = p_away / denom
    else:
        p_dnb_1 = p_dnb_2 = 0.5

    by_team = match.get("_season_by_team") or {}
    used_season = (
        estimate_lambdas_from_season(
            team_id_from_match(match, "home"),
            team_id_from_match(match, "away"),
            by_team,
        )
        is not None
    )

    missing = extract_missing(match)
    return {
        "w1": p_home,
        "x": p_draw,
        "w2": p_away,
        "btts_yes": p_btts_yes,
        "btts_no": p_btts_no,
        "dc_1x": p_home + p_draw,
        "dc_12": p_home + p_away,
        "dc_x2": p_draw + p_away,
        "total_over_25": p_over_25,
        "total_under_25": p_under_25,
        "dnb_1": p_dnb_1,
        "dnb_2": p_dnb_2,
        "_lambda_home": lh,
        "_lambda_away": la,
        "_used_season_strength": 1.0 if used_season else 0.0,
        "_missing_home": float(missing.home_count),
        "_missing_away": float(missing.away_count),
    }


def summarize_for_log(probs: dict[str, float]) -> dict[str, float]:
    return {k: round(v, 4) for k, v in probs.items() if not k.startswith("_")}
