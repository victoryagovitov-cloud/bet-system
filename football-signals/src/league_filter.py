from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import load_leagues_whitelist


def is_league_allowed(league_id: int | str | None) -> bool:
    """True, если лига в whitelist и data_quality != low."""
    if league_id is None:
        return False
    leagues = load_leagues_whitelist()
    meta = leagues.get(int(league_id))
    if not meta:
        return False
    return str(meta.get("data_quality", "medium")).lower() != "low"


def get_league_meta(league_id: int | str | None) -> dict | None:
    if league_id is None:
        return None
    return load_leagues_whitelist().get(int(league_id))
