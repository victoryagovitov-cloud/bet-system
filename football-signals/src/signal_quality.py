from __future__ import annotations

from typing import Any


# λ clip floors in probability_model — at the floor, totals/BTTS become fiction.
_LAMBDA_AWAY_FLOOR = 0.26
_LAMBDA_HOME_FLOOR = 0.36


def _best(odds_bk: dict, bookmakers: list[str], outcome: str) -> float | None:
    from src.value_engine import best_odds_across_bookmakers

    _, odds = best_odds_across_bookmakers(odds_bk, bookmakers, outcome)
    return odds


def market_disagreement_reason(
    odds_bk: dict,
    bookmakers: list[str],
    outcome: str,
    *,
    model_probs: dict[str, float] | None = None,
) -> str | None:
    """
    Skip value if we bet against the clear book favorite on the same family of markets.
    Returns human reason or None if aligned / not applicable.
    """
    if outcome in {"w1", "dnb_1", "dc_1x"}:
        w1 = _best(odds_bk, bookmakers, "w1")
        w2 = _best(odds_bk, bookmakers, "w2")
        if w1 is not None and w2 is not None and w1 > w2:
            return f"market favors away (w1@{w1:.2f} > w2@{w2:.2f})"
        return None

    if outcome in {"w2", "dnb_2", "dc_x2"}:
        w1 = _best(odds_bk, bookmakers, "w1")
        w2 = _best(odds_bk, bookmakers, "w2")
        if w1 is not None and w2 is not None and w2 > w1:
            return f"market favors home (w2@{w2:.2f} > w1@{w1:.2f})"
        return None

    if outcome == "total_under_25":
        over = _best(odds_bk, bookmakers, "total_over_25")
        under = _best(odds_bk, bookmakers, "total_under_25")
        if over is not None and under is not None and under > over:
            return f"market favors over (under@{under:.2f} > over@{over:.2f})"
        return None

    if outcome == "total_over_25":
        over = _best(odds_bk, bookmakers, "total_over_25")
        under = _best(odds_bk, bookmakers, "total_under_25")
        if over is not None and under is not None and over > under:
            return f"market favors under (over@{over:.2f} > under@{under:.2f})"
        return None

    if outcome == "btts_no":
        yes = _best(odds_bk, bookmakers, "btts_yes")
        no = _best(odds_bk, bookmakers, "btts_no")
        if yes is not None and no is not None and no > yes:
            return f"market favors BTTS yes (no@{no:.2f} > yes@{yes:.2f})"
        return None

    if outcome == "btts_yes":
        yes = _best(odds_bk, bookmakers, "btts_yes")
        no = _best(odds_bk, bookmakers, "btts_no")
        if yes is not None and no is not None and yes > no:
            return f"market favors BTTS no (yes@{yes:.2f} > no@{no:.2f})"
        return None

    return None


def lambda_floor_reason(outcome: str, model_probs: dict[str, float]) -> str | None:
    """Reject totals/BTTS when a team λ is glued to the model floor."""
    if outcome not in {"total_over_25", "total_under_25", "btts_yes", "btts_no"}:
        return None
    lh = model_probs.get("_lambda_home")
    la = model_probs.get("_lambda_away")
    if lh is not None and float(lh) <= _LAMBDA_HOME_FLOOR:
        return f"lambda_home at floor ({lh})"
    if la is not None and float(la) <= _LAMBDA_AWAY_FLOOR:
        return f"lambda_away at floor ({la})"
    return None


def quality_skip_reason(
    odds_bk: dict,
    bookmakers: list[str],
    outcome: str,
    model_prob: float,
    best_odds: float,
    *,
    min_edge: float,
    max_edge: float,
    model_probs: dict[str, float],
) -> str | None:
    if best_odds <= 1.0:
        return "odds<=1"
    implied = 1.0 / best_odds
    edge = float(model_prob) - implied
    if edge < min_edge:
        return f"edge {edge:.3f} < min {min_edge}"
    if edge > max_edge:
        return f"edge {edge:.3f} > max {max_edge} (model distrust)"
    floor = lambda_floor_reason(outcome, model_probs)
    if floor:
        return floor
    disagree = market_disagreement_reason(
        odds_bk, bookmakers, outcome, model_probs=model_probs
    )
    if disagree:
        return disagree
    return None
