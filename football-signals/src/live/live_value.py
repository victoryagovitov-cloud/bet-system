"""Live value scan: edge vs RU bookmakers on in-play odds."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.live.stats_parse import parse_match_statistics
from src.live.tempo_model import LiveModelResult, build_live_probs, pressure_side
from src.value_engine import (
    OUTCOME_LABELS,
    OUTCOME_MARKET_MAP,
    _team_name,
    get_outcome_odds,
)

# Conservative live market set for MVP.
LIVE_OUTCOMES = frozenset(
    {
        "total_over_25",
        "total_under_25",
        "btts_yes",
        "btts_no",
        "dc_1x",
        "dc_x2",
        "w1",
        "w2",
        "dnb_1",
        "dnb_2",
    }
)


@dataclass
class LiveCandidate:
    match_id: int
    home_team: str
    away_team: str
    league_id: int
    league_name: str
    minute: int
    score: str
    outcome: str
    outcome_label: str
    model_prob: float
    best_bookmaker: str
    best_odds: float
    edge: float
    lambda_home_remain: float
    lambda_away_remain: float
    tempo_home: float
    tempo_away: float
    reasons: list[str] = field(default_factory=list)
    signal_kind: str = "live"
    stats_summary: dict[str, Any] = field(default_factory=dict)


def _market_block(odds_bk: dict, bookmaker: str, outcome: str) -> dict | None:
    mapping = OUTCOME_MARKET_MAP.get(outcome)
    if not mapping:
        return None
    market_key, _, _ = mapping
    bk = odds_bk.get(bookmaker)
    if not isinstance(bk, dict):
        return None
    markets = bk.get("markets") or {}
    market = markets.get(market_key)
    return market if isinstance(market, dict) else None


def _live_odds_ok(odds_bk: dict, bookmaker: str, outcome: str) -> bool:
    """Skip suspended / explicitly non-live markets when flags exist."""
    market = _market_block(odds_bk, bookmaker, outcome)
    if market is None:
        return False
    if market.get("suspended") is True:
        return False
    # If provider marks live explicitly, require isLive != False.
    if "isLive" in market and market.get("isLive") is False:
        return False
    factor = get_outcome_odds(odds_bk, bookmaker, outcome)
    return factor is not None and factor > 1.01


def best_live_odds(
    odds_bk: dict, bookmaker_ids: list[str], outcome: str
) -> tuple[str | None, float | None]:
    best_bk = None
    best_odds = None
    for bk in bookmaker_ids:
        if not _live_odds_ok(odds_bk, bk, outcome):
            continue
        factor = get_outcome_odds(odds_bk, bk, outcome)
        if factor is None:
            continue
        if best_odds is None or factor > best_odds:
            best_odds = factor
            best_bk = bk
    return best_bk, best_odds


def _heuristic_reasons(
    match: dict,
    model: LiveModelResult,
    outcome: str,
) -> list[str]:
    reasons: list[str] = []
    stats = parse_match_statistics(match)
    press = pressure_side(stats)
    sh, sa = model.score_home, model.score_away

    if press == "home" and outcome in {"w1", "dc_1x", "dnb_1", "total_over_25", "btts_yes"}:
        reasons.append("home_pressure")
    if press == "away" and outcome in {"w2", "dc_x2", "dnb_2", "total_over_25", "btts_yes"}:
        reasons.append("away_pressure")
    if sh == sa == 0 and outcome in {"total_over_25", "btts_yes"} and press:
        reasons.append("scoreless_with_pressure")
    if abs(model.tempo_home - 1.0) >= 0.25 or abs(model.tempo_away - 1.0) >= 0.25:
        reasons.append(
            f"tempo h={model.tempo_home:.2f}/a={model.tempo_away:.2f}"
        )
    if stats is not None:
        if stats.home.xg is not None or stats.away.xg is not None:
            reasons.append(
                f"xG {stats.home.xg if stats.home.xg is not None else '—'}:"
                f"{stats.away.xg if stats.away.xg is not None else '—'}"
            )
    return reasons


def _stats_summary(match: dict) -> dict[str, Any]:
    stats = parse_match_statistics(match)
    if stats is None:
        return {}
    return {
        "period": stats.period,
        "home": dict(stats.home.values),
        "away": dict(stats.away.values),
    }


def evaluate_match(
    match: dict,
    bookmaker_ids: list[str],
    *,
    min_model_probability: float = 0.55,
    min_edge: float = 0.05,
    max_edge: float = 0.20,
    min_minute: int = 20,
    max_minute: int = 80,
    require_stats: bool = True,
    require_heuristic: bool = True,
) -> tuple[LiveCandidate | None, str | None]:
    """
    Evaluate one match detail payload.
    Returns (best candidate or None, skip_reason or None).
    """
    model = build_live_probs(
        match,
        min_minute=min_minute,
        max_minute=max_minute,
        require_stats=require_stats,
    )
    if model.skip_reason:
        return None, model.skip_reason

    odds_bk = match.get("oddsBk") or {}
    tournament = match.get("tournament") or {}
    league_id = int(tournament.get("id") or 0)
    league_name = (tournament.get("translations") or {}).get("ru") or tournament.get("name") or "?"
    candidates: list[LiveCandidate] = []

    for outcome in LIVE_OUTCOMES:
        model_prob = model.probs.get(outcome)
        if model_prob is None or float(model_prob) < min_model_probability:
            continue
        best_bk, best_odds = best_live_odds(odds_bk, bookmaker_ids, outcome)
        if best_bk is None or best_odds is None:
            continue
        implied = 1.0 / float(best_odds)
        edge = float(model_prob) - implied
        if edge < min_edge or edge > max_edge:
            continue
        reasons = _heuristic_reasons(match, model, outcome)
        if require_heuristic and not any(
            r.startswith("home_pressure")
            or r.startswith("away_pressure")
            or r == "scoreless_with_pressure"
            for r in reasons
        ):
            # Still allow totals/BTTS when tempo is clearly elevated on either side.
            tempo_hot = model.tempo_home >= 1.25 or model.tempo_away >= 1.25
            if outcome not in {"total_over_25", "btts_yes"} or not tempo_hot:
                continue
        candidates.append(
            LiveCandidate(
                match_id=int(match["id"]),
                home_team=_team_name(match.get("homeTeam")),
                away_team=_team_name(match.get("awayTeam")),
                league_id=league_id,
                league_name=league_name,
                minute=model.minute,
                score=f"{model.score_home}:{model.score_away}",
                outcome=outcome,
                outcome_label=OUTCOME_LABELS.get(outcome, outcome),
                model_prob=float(model_prob),
                best_bookmaker=best_bk,
                best_odds=float(best_odds),
                edge=float(edge),
                lambda_home_remain=model.lambda_home_remain,
                lambda_away_remain=model.lambda_away_remain,
                tempo_home=model.tempo_home,
                tempo_away=model.tempo_away,
                reasons=reasons,
                stats_summary=_stats_summary(match),
            )
        )

    if not candidates:
        # Distinguish "looked but nothing" vs earlier hard skips.
        if not odds_bk:
            return None, "no_odds_bk"
        return None, "no_edge_candidate"

    best = max(candidates, key=lambda c: c.edge)
    return best, None
