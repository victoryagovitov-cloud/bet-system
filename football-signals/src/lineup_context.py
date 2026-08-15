from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# Soft λ penalty per missing player by position (capped per side).
_POS_PENALTY = {
    "G": 0.18,
    "GK": 0.18,
    "D": 0.10,
    "M": 0.10,
    "F": 0.14,
}
_DEFAULT_PENALTY = 0.10
_MAX_SIDE_PENALTY = 0.35

# Hard skip: don't publish a signal that leans on a heavily depleted side.
_BLOCK_COUNT = 3
_BLOCK_WITH_KEY = 2  # GK or striker counts as "key"


@dataclass(frozen=True)
class MissingPlayer:
    name: str
    position: str
    reason: str


@dataclass(frozen=True)
class MissingSummary:
    home: tuple[MissingPlayer, ...]
    away: tuple[MissingPlayer, ...]

    @property
    def home_count(self) -> int:
        return len(self.home)

    @property
    def away_count(self) -> int:
        return len(self.away)

    def has_key(self, side: str) -> bool:
        players = self.home if side == "home" else self.away
        return any(p.position in {"G", "GK", "F"} for p in players)

    def compact(self) -> dict[str, Any]:
        def pack(players: tuple[MissingPlayer, ...]) -> list[dict[str, str]]:
            return [
                {"name": p.name, "position": p.position, "reason": p.reason}
                for p in players[:6]
            ]

        return {
            "home_count": self.home_count,
            "away_count": self.away_count,
            "home": pack(self.home),
            "away": pack(self.away),
        }


def _ru_or_name(player: dict) -> str:
    tr = (player.get("translations") or {}).get("ru")
    return str(tr or player.get("name") or "?").strip()


def _reason_label(item: dict) -> str:
    reason = item.get("reason") or {}
    tr = (reason.get("translations") or {}).get("ru")
    if tr:
        return str(tr)
    return str(reason.get("name") or reason.get("categoryKey") or item.get("type") or "missing")


def _parse_side(team_block: dict | None) -> tuple[MissingPlayer, ...]:
    if not isinstance(team_block, dict):
        return ()
    lineup = team_block.get("lineup") or {}
    raw = lineup.get("missingPlayers") or []
    if not isinstance(raw, list):
        return ()
    out: list[MissingPlayer] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        player = item.get("player") or {}
        if not isinstance(player, dict):
            continue
        pos = str(player.get("position") or "").upper().strip()
        out.append(
            MissingPlayer(
                name=_ru_or_name(player),
                position=pos,
                reason=_reason_label(item),
            )
        )
    return tuple(out)


def extract_missing(match: dict) -> MissingSummary:
    return MissingSummary(
        home=_parse_side(match.get("homeTeam")),
        away=_parse_side(match.get("awayTeam")),
    )


def _side_penalty(players: tuple[MissingPlayer, ...]) -> float:
    if not players:
        return 0.0
    total = 0.0
    for p in players:
        total += _POS_PENALTY.get(p.position, _DEFAULT_PENALTY)
    return min(_MAX_SIDE_PENALTY, total)


def lambda_penalties(summary: MissingSummary) -> tuple[float, float]:
    """Negative deltas applied to home/away attack λ."""
    return -_side_penalty(summary.home), -_side_penalty(summary.away)


def _favors_home(outcome: str) -> bool:
    return outcome in {"w1", "dc_1x", "dnb_1"}


def _favors_away(outcome: str) -> bool:
    return outcome in {"w2", "dc_x2", "dnb_2"}


def blocks_outcome(outcome: str, summary: MissingSummary) -> str | None:
    """
    Soft hard-stop: skip signals that bet on a side with heavy absences.
    Returns reason string or None.
    """
    if _favors_home(outcome):
        if summary.home_count >= _BLOCK_COUNT:
            return f"home missingPlayers={summary.home_count}"
        if summary.home_count >= _BLOCK_WITH_KEY and summary.has_key("home"):
            return f"home key missingPlayers={summary.home_count}"
    if _favors_away(outcome):
        if summary.away_count >= _BLOCK_COUNT:
            return f"away missingPlayers={summary.away_count}"
        if summary.away_count >= _BLOCK_WITH_KEY and summary.has_key("away"):
            return f"away key missingPlayers={summary.away_count}"
    return None
