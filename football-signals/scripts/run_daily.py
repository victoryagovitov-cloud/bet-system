#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loguru import logger

from config.settings import get_settings
from src.pipeline.daily_job import run_daily_pipeline


def _today_in_timezone(tz_name: str) -> date:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo(tz_name)).date()
    except Exception:
        # Windows without tzdata: MSK = UTC+3
        return (datetime.utcnow() + timedelta(hours=3)).date()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Daily football signals pipeline")
    p.add_argument(
        "--date",
        help="YYYY-MM-DD — только эта дата (иначе сегодня+завтра)",
    )
    p.add_argument(
        "--today",
        action="store_true",
        help="Только сегодня (без завтра)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings()
    now = _today_in_timezone(settings.timezone)

    if args.date:
        dates = [date.fromisoformat(args.date)]
    elif args.today:
        # Один день — сегодня
        dates = [now]
    else:
        # По умолчанию: сегодня + завтра — выше шанс, что в канале будет ставка,
        # а сводка уйдёт в любом случае.
        dates = [now, now + timedelta(days=1)]

    logger.info("run_daily dates={} publish_mode={}", dates, settings.publish_mode)
    signals = run_daily_pipeline(dates)
    print(
        f"signals_published={len(signals)} dates="
        + ",".join(d.isoformat() for d in dates)
    )
    for s in signals:
        print(
            f"- {s.home_team} vs {s.away_team} | {s.outcome_label} | "
            f"p={s.model_prob:.0%} | {s.best_bookmaker}@{s.best_odds} | "
            f"stake={s.stake_fraction:.2%}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
