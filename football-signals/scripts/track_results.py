#!/usr/bin/env python
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loguru import logger

from config.settings import get_settings
from src.api_sport_client import ApiSportClient, ApiSportError
from src.db.repository import SignalRepository
from src.metrics import calibration_report, compute_clv
from src.value_engine import best_odds_across_bookmakers


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

            # Capture closing line while match is finished (or late prematch if already started)
            closing_bk, closing_odds = best_odds_across_bookmakers(
                match.get("oddsBk") or {},
                settings.bookmakers_whitelist,
                row.outcome,
            )
            clv = None
            if closing_odds is not None:
                clv = compute_clv(float(row.best_odds), float(closing_odds))

            if match.get("status") != "finished":
                # Optionally still store closing odds later; skip settle for now
                continue

            home, away, score = _score_tuple(match)
            if home is None or away is None:
                continue
            won = _won(row.outcome, home, away)
            if won is None:
                continue
            repo.mark_settled(
                row.id,
                won,
                score,
                closing_odds=closing_odds,
                closing_bookmaker=closing_bk,
                clv=clv,
            )
            settled += 1
            logger.info(
                "settled #{} {} -> {} clv={}",
                row.id,
                score,
                "WIN" if won else "LOSS",
                None if clv is None else round(clv, 4),
            )

    report = calibration_report(repo.settled_published())
    print(f"settled_now={settled}")
    print(
        json.dumps(
            {
                "n": report.n,
                "hit_rate": report.hit_rate,
                "mean_model_prob": report.mean_model_prob,
                "brier": report.brier,
                "mean_clv": report.mean_clv,
                "by_league": {
                    str(k): v for k, v in report.by_league.items()
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if report.n >= 20 and report.mean_model_prob and report.hit_rate is not None:
        gap = report.mean_model_prob - report.hit_rate
        if gap > 0.10:
            logger.warning(
                "calibration gap: model mean {:.0%} vs hit-rate {:.0%} — model may be overconfident",
                report.mean_model_prob,
                report.hit_rate,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
