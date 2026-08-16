"""Parse API-SPORT matchStatistics into flat home/away numeric maps."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Keys we care about for live tempo / pressure heuristics.
LIVE_STAT_KEYS = frozenset(
    {
        "ballPossession",
        "expectedGoals",
        "bigChanceCreated",
        "bigChanceMissed",
        "totalShotsOnGoal",
        "shotsOnGoal",
        "shotsOffGoal",
        "cornerKicks",
        "redCards",
        "yellowCards",
        "goalkeeperSaves",
        "totalShotsInsideBox",
        "blockedScoringAttempt",
    }
)


@dataclass
class TeamLiveStats:
    values: dict[str, float] = field(default_factory=dict)

    def get(self, key: str, default: float = 0.0) -> float:
        return float(self.values.get(key, default))

    @property
    def xg(self) -> float | None:
        if "expectedGoals" not in self.values:
            return None
        return self.values["expectedGoals"]

    @property
    def shots_total(self) -> float:
        return self.get("totalShotsOnGoal")

    @property
    def shots_on_target(self) -> float:
        return self.get("shotsOnGoal")

    @property
    def possession(self) -> float | None:
        if "ballPossession" not in self.values:
            return None
        return self.values["ballPossession"]

    @property
    def red_cards(self) -> float:
        return self.get("redCards")

    @property
    def has_attack_signal(self) -> bool:
        """True if we have at least one usable attack metric."""
        return (
            self.xg is not None
            or self.shots_total > 0
            or self.shots_on_target > 0
            or self.get("bigChanceCreated") > 0
        )


@dataclass
class MatchLiveStats:
    home: TeamLiveStats = field(default_factory=TeamLiveStats)
    away: TeamLiveStats = field(default_factory=TeamLiveStats)
    period: str = "ALL"

    @property
    def has_usable_stats(self) -> bool:
        return self.home.has_attack_signal or self.away.has_attack_signal


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip().replace("%", "").replace(",", ".")
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _merge_item(home: dict[str, float], away: dict[str, float], item: dict) -> None:
    key = item.get("key")
    if not key or key not in LIVE_STAT_KEYS:
        return
    hv = _as_float(item.get("homeValue"))
    av = _as_float(item.get("awayValue"))
    if hv is None:
        hv = _as_float(item.get("home"))
    if av is None:
        av = _as_float(item.get("away"))
    if hv is not None:
        home[str(key)] = hv
    if av is not None:
        away[str(key)] = av


def parse_match_statistics(
    match: dict,
    *,
    prefer_period: str = "ALL",
) -> MatchLiveStats | None:
    """
    Extract team stats from match['matchStatistics'].
    Prefer period ALL; fall back to first available period with items.
    """
    periods = match.get("matchStatistics") or []
    if not isinstance(periods, list) or not periods:
        return None

    chosen: dict | None = None
    for block in periods:
        if isinstance(block, dict) and str(block.get("period") or "").upper() == prefer_period.upper():
            chosen = block
            break
    if chosen is None:
        for block in periods:
            if isinstance(block, dict):
                chosen = block
                break
    if not chosen:
        return None

    home: dict[str, float] = {}
    away: dict[str, float] = {}
    for group in chosen.get("groups") or []:
        if not isinstance(group, dict):
            continue
        for item in group.get("statisticsItems") or []:
            if isinstance(item, dict):
                _merge_item(home, away, item)

    if not home and not away:
        return None

    return MatchLiveStats(
        home=TeamLiveStats(values=home),
        away=TeamLiveStats(values=away),
        period=str(chosen.get("period") or prefer_period),
    )


def current_score(match: dict) -> tuple[int | None, int | None]:
    hs = match.get("homeScore") or {}
    aws = match.get("awayScore") or {}
    if not isinstance(hs, dict):
        hs = {}
    if not isinstance(aws, dict):
        aws = {}
    home = hs.get("current")
    away = aws.get("current")
    if home is None:
        home = hs.get("display")
    if away is None:
        away = aws.get("display")
    try:
        return (int(home) if home is not None else None, int(away) if away is not None else None)
    except (TypeError, ValueError):
        return None, None


def current_minute(match: dict) -> int | None:
    raw = match.get("currentMatchMinute")
    if raw is None:
        return None
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return None


def count_red_cards_from_events(match: dict) -> tuple[int, int]:
    """Count non-rescinded red cards from liveEvents (home, away)."""
    home = away = 0
    for ev in match.get("liveEvents") or []:
        if not isinstance(ev, dict):
            continue
        if str(ev.get("type") or "").lower() != "card":
            continue
        if ev.get("rescinded"):
            continue
        cls = str(ev.get("class") or "").lower()
        # API uses class values like "red", "yellowRed"
        if "red" not in cls:
            continue
        team = str(ev.get("team") or "").lower()
        if team == "home":
            home += 1
        elif team == "away":
            away += 1
    return home, away
