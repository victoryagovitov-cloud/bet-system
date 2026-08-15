#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loguru import logger

from config.settings import get_settings
from src import max_publisher, signal_formatter
from src.settlement import settle_pending


def main() -> int:
    parser = argparse.ArgumentParser(description="Settle finished signals + optional MAX status")
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish compact accounting status to MAX (or dry-run file)",
    )
    args = parser.parse_args()

    settings = get_settings()
    snap = settle_pending(settings)
    payload = snap.to_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.publish:
        text = signal_formatter.format_accounting_report(snap)
        ref = max_publisher.publish_signal(
            text,
            chat_id=settings.max_channel_chat_id,
            token=settings.max_bot_token,
            publish_mode=settings.publish_mode,
            match_id=None,
        )
        logger.info("accounting report published ref={}", ref)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
