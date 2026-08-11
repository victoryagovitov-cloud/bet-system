#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loguru import logger

from config.settings import get_settings
from src.api_sport_client import ApiSportClient, ApiSportError
from src.db.repository import SignalRepository


def _score_tuple(match: dict) -> tuple[int | None, int | None, str | None]:
    hs = match.get("homeScore") or {}
    as_ = match.get("awayScore") or {}
    home = hs.get("current")
    away = as_.get("current")
    if home is None:
        home = hs.get("display")
    if away is None:
        away = as_.get("display")
    try:
        home_i = int(home) if home is not None else None
        away_i = int(away) if away is not None else None
    except (TypeError, ValueError):
        return None, None, None
    if home_i is None or away_i is None:
        return None, None, None
    return home_i, away_i, f"{home_i}:{away_i}"


def _won(outcome: str, home: int, away: int) -> bool | None:
    if outcome == "w1":
        return home > away
    if outcome == "x":
        return home == away
    if outcome == "w2":
        return home < away
    if outcome == "dc_1x":
        return home >= away
    if outcome == "dc_x2":
        return home <= away
    if outcome == "dc_12":
        return home != away
    if outcome == "btts_yes":
        return home > 0 and away > 0
    if outcome == "btts_no":
        return home == 0 or away == 0
    return None


def main() -> int:
    settings = get_settings()
    repo = SignalRepository(settings.database_url)
    rows = repo.unsettled()
    if not rows:
        print("no unsettled signals")
        return 0

    settled = 0
    with ApiSportClient(
        settings.api_sport_base_url,
        settings.api_sport_key,
        settings.api_sport_sport_slug,
    ) as client:
        for row in rows:
            try:
                match = client.get_match_detail(row.match_id, settings.bookmakers_whitelist)
            except ApiSportError as exc:
                logger.warning("cannot fetch match {}: {}", row.match_id, exc)
                continue
            if match.get("status") != "finished":
                continue
            home, away, score = _score_tuple(match)
            if home is None or away is None:
                continue
            won = _won(row.outcome, home, away)
            if won is None:
                continue
            repo.mark_settled(row.id, won, score)
            settled += 1
            logger.info("settled #{} {} -> {}", row.id, score, "WIN" if won else "LOSS")

    print(f"settled={settled}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
