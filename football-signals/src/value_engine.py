from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SignalCandidate:
    match_id: int
    home_team: str
    away_team: str
    league_id: int
    league_name: str
    kickoff: str | None
    outcome: str
    outcome_label: str
    model_prob: float
    best_bookmaker: str
    best_odds: float
    edge: float
    stake_fraction: float = 0.0
    lambda_home: float | None = None
    lambda_away: float | None = None


# (market_key, stake_key, line_argument|None)
OUTCOME_MARKET_MAP: dict[str, tuple[str, str, float | None]] = {
    "w1": ("result", "w1", None),
    "x": ("result", "x", None),
    "w2": ("result", "w2", None),
    "btts_yes": ("btts", "yes", None),
    "btts_no": ("btts", "no", None),
    "dc_1x": ("double_chance", "1x", None),
    "dc_12": ("double_chance", "12", None),
    "dc_x2": ("double_chance", "x2", None),
    "total_over_25": ("total", "over", 2.5),
    "total_under_25": ("total", "under", 2.5),
    # European handicap 0 ≈ DNB (ничья — возврат)
    "dnb_1": ("handicap", "handicap_1", 0.0),
    "dnb_2": ("handicap", "handicap_2", 0.0),
}

OUTCOME_LABELS = {
    "w1": "П1",
    "x": "X",
    "w2": "П2",
    "btts_yes": "Обе забьют — да",
    "btts_no": "Обе забьют — нет",
    "dc_1x": "1X",
    "dc_12": "12",
    "dc_x2": "X2",
    "total_over_25": "ТБ 2.5",
    "total_under_25": "ТМ 2.5",
    "dnb_1": "DNB П1",
    "dnb_2": "DNB П2",
}


def _team_name(team: dict | None) -> str:
    if not team:
        return "?"
    return (team.get("translations") or {}).get("ru") or team.get("name") or "?"


def _extract_factor(stake_obj: Any, argument: float | None = None) -> float | None:
    if stake_obj is None:
        return None
    if isinstance(stake_obj, (int, float)):
        return float(stake_obj)
    if not isinstance(stake_obj, dict):
        return None
    if argument is None:
        if "factor" in stake_obj and stake_obj["factor"] is not None:
            try:
                return float(stake_obj["factor"])
            except (TypeError, ValueError):
                return None
        return None

    lines = stake_obj.get("lines")
    if not isinstance(lines, list):
        return None
    target = float(argument)
    for line in lines:
        try:
            if abs(float(line.get("argument")) - target) < 1e-9:
                return float(line.get("factor"))
        except (TypeError, ValueError, AttributeError):
            continue
    return None


def get_outcome_odds(odds_bk: dict, bookmaker: str, outcome: str) -> float | None:
    mapping = OUTCOME_MARKET_MAP.get(outcome)
    if not mapping:
        return None
    market_key, stake_key, argument = mapping
    bk = odds_bk.get(bookmaker)
    if not isinstance(bk, dict):
        return None
    if bk.get("isBettingActive") is False:
        return None
    markets = bk.get("markets") or {}
    market = markets.get(market_key) or {}
    stakes = market.get("stakes") or {}
    stake = stakes.get(stake_key)
    if stake is None and stake_key == "yes":
        stake = stakes.get("y") or stakes.get("btts_yes")
    if stake is None and stake_key == "no":
        stake = stakes.get("n") or stakes.get("btts_no")
    return _extract_factor(stake, argument)


def best_odds_across_bookmakers(
    odds_bk: dict, bookmaker_ids: list[str], outcome: str
) -> tuple[str | None, float | None]:
    best_bk = None
    best_odds = None
    for bk in bookmaker_ids:
        factor = get_outcome_odds(odds_bk, bk, outcome)
        if factor is None:
            continue
        if best_odds is None or factor > best_odds:
            best_odds = factor
            best_bk = bk
    return best_bk, best_odds


def odds_spread_for_outcome(
    odds_bk: dict, bookmaker_ids: list[str], outcome: str
) -> tuple[float | None, float | None, float | None]:
    """Return (min_odds, max_odds, spread=max-min) across active bookmakers."""
    factors: list[float] = []
    for bk in bookmaker_ids:
        factor = get_outcome_odds(odds_bk, bk, outcome)
        if factor is not None:
            factors.append(factor)
    if not factors:
        return None, None, None
    lo, hi = min(factors), max(factors)
    return lo, hi, hi - lo


def find_signal(
    match: dict,
    model_probs: dict[str, float],
    bookmaker_ids: list[str],
    min_model_probability: float = 0.80,
) -> SignalCandidate | None:
    """
    Берём исходы с P_model >= threshold, положительным edge против лучшего из 4 БК,
    публикуем один исход на матч — с максимальным edge.
    """
    odds_bk = match.get("oddsBk") or {}
    candidates: list[SignalCandidate] = []

    tournament = match.get("tournament") or {}
    league_id = int(tournament.get("id") or 0)
    league_name = (tournament.get("translations") or {}).get("ru") or tournament.get("name") or "?"

    for outcome, model_prob in model_probs.items():
        if outcome.startswith("_"):
            continue
        if outcome not in OUTCOME_MARKET_MAP:
            continue
        if model_prob < min_model_probability:
            continue
        best_bk, best_odds = best_odds_across_bookmakers(odds_bk, bookmaker_ids, outcome)
        if best_bk is None or best_odds is None or best_odds <= 1.0:
            continue
        implied = 1.0 / best_odds
        edge = model_prob - implied
        if edge <= 0:
            continue
        candidates.append(
            SignalCandidate(
                match_id=int(match["id"]),
                home_team=_team_name(match.get("homeTeam")),
                away_team=_team_name(match.get("awayTeam")),
                league_id=league_id,
                league_name=league_name,
                kickoff=match.get("dateEvent"),
                outcome=outcome,
                outcome_label=OUTCOME_LABELS.get(outcome, outcome),
                model_prob=float(model_prob),
                best_bookmaker=best_bk,
                best_odds=float(best_odds),
                edge=float(edge),
                lambda_home=model_probs.get("_lambda_home"),
                lambda_away=model_probs.get("_lambda_away"),
            )
        )

    if not candidates:
        return None
    return max(candidates, key=lambda c: c.edge)
