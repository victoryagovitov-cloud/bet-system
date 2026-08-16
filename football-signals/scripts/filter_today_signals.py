#!/usr/bin/env python
"""Retrospectively apply quality filters to today's published VALUE signals."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loguru import logger

from config.settings import get_settings
from src import max_publisher
from src.api_sport_client import ApiSportClient, ApiSportError
from src.db.repository import SignalRepository
from src.signal_quality import quality_skip_reason
from src.value_engine import best_odds_across_bookmakers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true", help="Post keep/drop note to MAX")
    parser.add_argument(
        "--since-hours",
        type=int,
        default=18,
        help="Look back window for published signals (default 18h)",
    )
    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    settings = get_settings()
    repo = SignalRepository(settings.database_url)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=args.since_hours)
    rows = [
        r
        for r in repo.list_published_since(since)
        if (r.signal_kind or "value") == "value"
    ]
    if not rows:
        print("no recent value signals")
        return 0

    keep: list[str] = []
    drop: list[str] = []

    with ApiSportClient(
        settings.api_sport_base_url,
        settings.api_sport_key,
        settings.api_sport_sport_slug,
    ) as client:
        for row in rows:
            try:
                detail = client.get_match_detail(int(row.match_id), settings.bookmakers_whitelist)
            except ApiSportError as exc:
                logger.warning("cannot fetch {}: {}", row.match_id, exc)
                continue
            odds_bk = detail.get("oddsBk") or {}
            best_bk, best_odds = best_odds_across_bookmakers(
                odds_bk, settings.bookmakers_whitelist, row.outcome
            )
            if best_odds is None:
                best_odds = float(row.best_odds)
            model_probs = {
                row.outcome: float(row.model_prob),
                "_lambda_home": 1.0,
                "_lambda_away": 1.0,
            }
            # Re-check market/edge only (λ floors need live λ — soft skip if unknown)
            skip = quality_skip_reason(
                odds_bk,
                settings.bookmakers_whitelist,
                row.outcome,
                float(row.model_prob),
                float(best_odds),
                min_edge=settings.min_edge,
                max_edge=settings.max_edge,
                model_probs=model_probs,
            )
            line = (
                f"{row.home_team} — {row.away_team}: {row.outcome_label} "
                f"(P={row.model_prob:.0%}, edge={row.edge:.1%})"
            )
            if skip:
                repo.update_status(
                    int(row.id),
                    "filtered_quality",
                    note=f"posthoc: {skip}",
                )
                drop.append(f"— {line} [{skip}]")
                logger.info("DROP #{} {}", row.id, skip)
            else:
                keep.append(f"— {line}")
                logger.info("KEEP #{}", row.id)

    msk = datetime.now(ZoneInfo(settings.timezone)).strftime("%Y-%m-%d %H:%M")
    text = (
        "УТОЧНЕНИЕ ПО УТРЕННИМ VALUE\n"
        "────────\n"
        f"Время: {msk}\n"
        "Часть сигналов отсеяна новыми правилами: "
        "не спорим с рынком, edge не выше потолка, лимит на прогон.\n\n"
        f"Оставляем в учёте ({len(keep)}):\n"
        + ("\n".join(keep) if keep else "— нет")
        + f"\n\nСнимаем с учёта ({len(drop)}):\n"
        + ("\n".join(drop[:20]) if drop else "— нет")
        + "\n\nДальше эти фильтры работают автоматически."
    )
    print(text)
    if args.publish:
        ref = max_publisher.publish_signal(
            text,
            chat_id=settings.max_channel_chat_id,
            token=settings.max_bot_token,
            publish_mode=settings.publish_mode,
        )
        logger.info("clarification published ref={}", ref)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
