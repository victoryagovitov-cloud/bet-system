"""Find in-progress football matches from API-SPORT REST list."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Callable

from src.league_filter import is_league_allowed

# Terminal / pre-match statuses — everything else is treated as in-play-ish.
_SKIP_STATUSES = frozenset(
    {
        "notstarted",
        "finished",
        "canceled",
        "cancelled",
        "postponed",
        "abandoned",
        "interrupted",  # often not bettable; still skip by default
    }
)


def _status(match: dict) -> str:
    return str(match.get("status") or "").lower()


def is_inplay_status(match: dict) -> bool:
    st = _status(match)
    if st in _SKIP_STATUSES:
        return False
    # Prefer explicit inprogress; also accept delayed/suspended/willcontinue
    # only when a minute/score suggests the match has started.
    if st == "inprogress":
        return True
    minute = match.get("currentMatchMinute")
    if minute is not None:
        try:
            return int(minute) >= 0 and st not in {"notstarted", "finished"}
        except (TypeError, ValueError):
            pass
    return False


def list_inplay_matches(
    matches: list[dict],
    *,
    whitelist_only: bool = True,
    league_ok: Callable[[Any], bool] | None = None,
) -> list[dict]:
    """Filter a flat match list down to in-play rows."""
    check = league_ok or is_league_allowed
    out: list[dict] = []
    for m in matches:
        if not is_inplay_status(m):
            continue
        tid = (m.get("tournament") or {}).get("id")
        if whitelist_only and not check(tid):
            continue
        out.append(m)
    return out


def collect_inplay_for_dates(
    get_matches: Callable[[date], list[dict]],
    *,
    days: int = 1,
    start: date | None = None,
    whitelist_only: bool = True,
) -> list[dict]:
    """
    Pull matches for today (+ optional next days) and keep in-play whitelist rows.
    `get_matches(d)` should already apply bookmaker filter at the client layer.
    """
    start = start or date.today()
    seen: set[int] = set()
    rows: list[dict] = []
    for offset in range(max(1, days)):
        target = start + timedelta(days=offset)
        for m in list_inplay_matches(get_matches(target), whitelist_only=whitelist_only):
            mid = m.get("id")
            try:
                mid_i = int(mid)
            except (TypeError, ValueError):
                continue
            if mid_i in seen:
                continue
            seen.add(mid_i)
            rows.append(m)
    return rows
