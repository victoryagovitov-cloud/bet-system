from __future__ import annotations

import re
from typing import Any

import numpy as np
from scipy.stats import poisson

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


def _form_attack_shift(form: Any, side: str) -> float:
    """
    Сдвиг λ по строке формы (W/D/L). Поддерживает:
    - dict {"home": "WWDLW", "away": "..."}
    - dict с ключами homeForm/awayForm
    - строку только если side совпадает с единственным полем
    """
    if not form:
        return 0.0
    raw = None
    if isinstance(form, dict):
        raw = (
            form.get(side)
            or form.get(f"{side}Form")
            or form.get(f"{side}_form")
            or form.get("home" if side == "home" else "away")
        )
        if isinstance(raw, dict):
            raw = raw.get("form") or raw.get("string") or raw.get("value")
    elif isinstance(form, str) and side == "home":
        raw = form
    if not isinstance(raw, str) or not raw.strip():
        return 0.0
    letters = [c.upper() for c in raw if c.upper() in {"W", "D", "L"}][-5:]
    if not letters:
        return 0.0
    points = sum(3 if c == "W" else 1 if c == "D" else 0 for c in letters)
    avg = points / (3 * len(letters))  # 0..1
    return (avg - 0.5) * 0.35


def _estimate_lambdas(match: dict) -> tuple[float, float]:
    """
    Независимая оценка ожидаемых голов по pregame (h2h + streaks + form).
    Коэффициенты букмекеров НЕ используются.
    """
    pregame = match.get("pregame") or {}
    h2h = ((pregame.get("h2h") or {}).get("teamDuel")) or {}
    home_wins = float(h2h.get("homeWins") or 0)
    away_wins = float(h2h.get("awayWins") or 0)
    draws = float(h2h.get("draws") or 0)
    total = home_wins + away_wins + draws

    # Базовые λ для «среднего» матча топ-лиги + home advantage
    lambda_home = 1.35
    lambda_away = 1.10

    if total >= 3:
        home_share = (home_wins + 0.5 * draws) / total
        # переводим доминирование в сдвиг голов
        lambda_home += (home_share - 0.5) * 1.2
        lambda_away += ((1.0 - home_share) - 0.5) * 1.2

    home_s, away_s = _streak_maps(pregame)

    def apply_over(streaks: dict[str, float], base: float) -> float:
        over = streaks.get("more than 2.5 goals")
        if over is not None:
            # 0..1 -> сдвиг ±0.35 вокруг 1.25
            base += (over - 0.55) * 0.7
        btts = streaks.get("both teams scoring")
        if btts is not None:
            base += (btts - 0.5) * 0.25
        losses = streaks.get("losses")
        if losses is not None and losses >= 3:
            base -= 0.15
        wins = streaks.get("wins")
        if wins is not None and wins >= 3:
            base += min(0.20, 0.05 * wins)
        no_losses = streaks.get("no losses")
        if no_losses is not None and no_losses >= 4:
            base += 0.08
        first = streaks.get("first to score")
        if first is not None and first >= 0.7:
            base += 0.10
        return base

    lambda_home = apply_over(home_s, lambda_home)
    lambda_away = apply_over(away_s, lambda_away)

    # серии без сухих / пропусков
    if away_s.get("without clean sheet", 0) >= 5:
        lambda_home += 0.15
    if home_s.get("without clean sheet", 0) >= 5:
        lambda_away += 0.15
    if home_s.get("no goals conceded", 0) >= 3:
        lambda_away -= 0.12
    if away_s.get("no goals conceded", 0) >= 3:
        lambda_home -= 0.12

    form = pregame.get("form")
    lambda_home += _form_attack_shift(form, "home")
    lambda_away += _form_attack_shift(form, "away")

    lambda_home = float(np.clip(lambda_home, 0.35, 3.2))
    lambda_away = float(np.clip(lambda_away, 0.25, 3.0))
    return lambda_home, lambda_away


def _score_matrix(lambda_home: float, lambda_away: float, max_goals: int = MAX_GOALS) -> np.ndarray:
    # Независимый Пуассон (Dixon–Coles rho=0 на MVP; можно добавить позже)
    home_probs = poisson.pmf(np.arange(0, max_goals + 1), lambda_home)
    away_probs = poisson.pmf(np.arange(0, max_goals + 1), lambda_away)
    matrix = np.outer(home_probs, away_probs)
    # хвост «6+» уже частично учтён усечением; нормализуем
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

    # matrix[i, j] = P(home=i, away=j)
    p_home = float(sum(matrix[i, j] for i in range(matrix.shape[0]) for j in range(matrix.shape[1]) if i > j))
    p_draw = float(np.trace(matrix))
    p_away = float(sum(matrix[i, j] for i in range(matrix.shape[0]) for j in range(matrix.shape[1]) if i < j))

    # numerical normalize 1X2
    s = p_home + p_draw + p_away
    p_home, p_draw, p_away = p_home / s, p_draw / s, p_away / s

    p_btts_yes = float(
        sum(matrix[i, j] for i in range(1, matrix.shape[0]) for j in range(1, matrix.shape[1]))
    )
    p_btts_no = 1.0 - p_btts_yes

    # Totals 2.5
    p_over_25 = float(
        sum(matrix[i, j] for i in range(matrix.shape[0]) for j in range(matrix.shape[1]) if i + j >= 3)
    )
    p_under_25 = 1.0 - p_over_25

    # Draw No Bet (exclude draws)
    denom = p_home + p_away
    if denom > 0:
        p_dnb_1 = p_home / denom
        p_dnb_2 = p_away / denom
    else:
        p_dnb_1 = p_dnb_2 = 0.5

    probs = {
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
    }
    return probs


def summarize_for_log(probs: dict[str, float]) -> dict[str, float]:
    return {k: round(v, 4) for k, v in probs.items() if not k.startswith("_")}
