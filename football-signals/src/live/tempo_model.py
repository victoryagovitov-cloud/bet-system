"""In-play tempo model: prematch λ × live tempo → remaining-time outcome probs."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.live.stats_parse import (
    MatchLiveStats,
    count_red_cards_from_events,
    current_minute,
    current_score,
    parse_match_statistics,
)
from src.probability_model import _score_matrix, compute


@dataclass(frozen=True)
class LiveModelResult:
    probs: dict[str, float]
    lambda_home_90: float
    lambda_away_90: float
    lambda_home_remain: float
    lambda_away_remain: float
    minute: int
    score_home: int
    score_away: int
    tempo_home: float
    tempo_away: float
    skip_reason: str | None = None


def _tempo_multiplier(
    observed: float | None,
    expected: float,
    *,
    floor: float = 0.6,
    ceil: float = 1.6,
) -> float:
    if observed is None or expected <= 1e-9:
        return 1.0
    return float(np.clip(observed / expected, floor, ceil))


def _attack_observed(side: MatchLiveStats, which: str) -> float | None:
    team = side.home if which == "home" else side.away
    # Prefer xG; blend soft shots signal when xG missing.
    if team.xg is not None:
        return float(team.xg)
    shots = team.shots_on_target + 0.35 * team.shots_total
    if shots <= 0:
        return None
    # Rough shots→xG proxy so tempo is not blank when xG absent.
    return 0.12 * shots


def build_live_probs(
    match: dict,
    *,
    min_minute: int = 20,
    max_minute: int = 80,
    require_stats: bool = True,
    injury_buffer_min: int = 2,
) -> LiveModelResult:
    """
    Scale prematch λ to remaining minutes, adjust by live xG/shots tempo,
    then fold remaining Poisson goals onto the current score.
    """
    minute = current_minute(match)
    sh, sa = current_score(match)
    base = compute(match)
    lh90 = float(base.get("_lambda_home") or 1.0)
    la90 = float(base.get("_lambda_away") or 1.0)

    if minute is None or sh is None or sa is None:
        return LiveModelResult(
            probs={},
            lambda_home_90=lh90,
            lambda_away_90=la90,
            lambda_home_remain=0.0,
            lambda_away_remain=0.0,
            minute=minute or 0,
            score_home=sh or 0,
            score_away=sa or 0,
            tempo_home=1.0,
            tempo_away=1.0,
            skip_reason="no_minute_or_score",
        )

    if minute < min_minute or minute > max_minute:
        return LiveModelResult(
            probs={},
            lambda_home_90=lh90,
            lambda_away_90=la90,
            lambda_home_remain=0.0,
            lambda_away_remain=0.0,
            minute=minute,
            score_home=sh,
            score_away=sa,
            tempo_home=1.0,
            tempo_away=1.0,
            skip_reason=f"minute_out_of_window:{minute}",
        )

    stats = parse_match_statistics(match)
    if require_stats and (stats is None or not stats.has_usable_stats):
        return LiveModelResult(
            probs={},
            lambda_home_90=lh90,
            lambda_away_90=la90,
            lambda_home_remain=0.0,
            lambda_away_remain=0.0,
            minute=minute,
            score_home=sh,
            score_away=sa,
            tempo_home=1.0,
            tempo_away=1.0,
            skip_reason="no_usable_stats",
        )

    played = max(float(minute), 1.0)
    remain = max(90.0 + float(injury_buffer_min) - played, 1.0)
    remain_frac = remain / 90.0
    played_frac = played / 90.0

    obs_h = _attack_observed(stats, "home") if stats else None
    obs_a = _attack_observed(stats, "away") if stats else None
    exp_h = lh90 * played_frac
    exp_a = la90 * played_frac
    tempo_h = _tempo_multiplier(obs_h, exp_h)
    tempo_a = _tempo_multiplier(obs_a, exp_a)

    # Red cards: prefer events, fall back to statistics.
    red_h, red_a = count_red_cards_from_events(match)
    if stats is not None:
        red_h = max(red_h, int(stats.home.red_cards))
        red_a = max(red_a, int(stats.away.red_cards))
    # Numerical disadvantage → suppress that side's remaining λ.
    if red_h > red_a:
        tempo_h *= 0.72 ** (red_h - red_a)
        tempo_a *= 1.12 ** (red_h - red_a)
    elif red_a > red_h:
        tempo_a *= 0.72 ** (red_a - red_h)
        tempo_h *= 1.12 ** (red_a - red_h)

    lh_rem = float(np.clip(lh90 * remain_frac * tempo_h, 0.02, 3.5))
    la_rem = float(np.clip(la90 * remain_frac * tempo_a, 0.02, 3.5))

    rem_matrix = _score_matrix(lh_rem, la_rem)
    probs = _final_outcome_probs(sh, sa, rem_matrix)
    probs["_lambda_home"] = lh90
    probs["_lambda_away"] = la90
    probs["_lambda_home_remain"] = lh_rem
    probs["_lambda_away_remain"] = la_rem
    probs["_tempo_home"] = tempo_h
    probs["_tempo_away"] = tempo_a
    probs["_minute"] = float(minute)
    probs["_score_home"] = float(sh)
    probs["_score_away"] = float(sa)

    return LiveModelResult(
        probs=probs,
        lambda_home_90=lh90,
        lambda_away_90=la90,
        lambda_home_remain=lh_rem,
        lambda_away_remain=la_rem,
        minute=minute,
        score_home=sh,
        score_away=sa,
        tempo_home=tempo_h,
        tempo_away=tempo_a,
        skip_reason=None,
    )


def _final_outcome_probs(
    score_home: int,
    score_away: int,
    rem_matrix: np.ndarray,
) -> dict[str, float]:
    """Map remaining-goal matrix onto final match outcomes from current score."""
    p_home = p_draw = p_away = 0.0
    p_btts_yes = p_over_25 = 0.0
    already_btts = score_home > 0 and score_away > 0
    base_goals = score_home + score_away

    for i in range(rem_matrix.shape[0]):
        for j in range(rem_matrix.shape[1]):
            p = float(rem_matrix[i, j])
            fh = score_home + i
            fa = score_away + j
            if fh > fa:
                p_home += p
            elif fh == fa:
                p_draw += p
            else:
                p_away += p
            if already_btts or (fh > 0 and fa > 0):
                p_btts_yes += p
            if fh + fa >= 3:
                p_over_25 += p

    s = p_home + p_draw + p_away
    if s <= 0:
        p_home = p_draw = p_away = 1.0 / 3.0
    else:
        p_home, p_draw, p_away = p_home / s, p_draw / s, p_away / s

    denom = p_home + p_away
    if denom > 0:
        p_dnb_1 = p_home / denom
        p_dnb_2 = p_away / denom
    else:
        p_dnb_1 = p_dnb_2 = 0.5

    return {
        "w1": p_home,
        "x": p_draw,
        "w2": p_away,
        "btts_yes": p_btts_yes,
        "btts_no": 1.0 - p_btts_yes,
        "dc_1x": p_home + p_draw,
        "dc_12": p_home + p_away,
        "dc_x2": p_draw + p_away,
        "total_over_25": p_over_25,
        "total_under_25": 1.0 - p_over_25,
        "dnb_1": p_dnb_1,
        "dnb_2": p_dnb_2,
        "_base_goals": float(base_goals),
    }


def pressure_side(stats: MatchLiveStats | None) -> str | None:
    """Return 'home' / 'away' if one side clearly dominates attack metrics."""
    if stats is None:
        return None
    h_xg = stats.home.xg or 0.0
    a_xg = stats.away.xg or 0.0
    h_sot = stats.home.shots_on_target
    a_sot = stats.away.shots_on_target
    h_score = h_xg * 1.5 + h_sot + 0.25 * stats.home.shots_total
    a_score = a_xg * 1.5 + a_sot + 0.25 * stats.away.shots_total
    if h_score >= a_score + 1.2 and h_score >= 1.0:
        return "home"
    if a_score >= h_score + 1.2 and a_score >= 1.0:
        return "away"
    return None
