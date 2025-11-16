#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

log_file = Path("data/recommendations_log.csv")
if not log_file.exists():
    print("Лог не найден")
    exit(0)

now = datetime.now(ZoneInfo("Europe/Moscow"))
cutoff = now - timedelta(hours=2)

print("=" * 70)
print("ПОСЛЕДНИЕ ЗАПИСИ В ЛОГЕ (последние 2 часа)")
print("=" * 70)

with log_file.open("r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    
    recent = []
    for row in rows:
        timestamp_str = row.get("timestamp_msk", "")
        if not timestamp_str:
            continue
        try:
            row_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            row_time = row_time.replace(tzinfo=ZoneInfo("Europe/Moscow"))
            if row_time >= cutoff:
                recent.append(row)
        except (ValueError, TypeError):
            continue
    
    print(f"\nВсего записей за последние 2 часа: {len(recent)}")
    
    # Ищем конкретный матч
    target_slug = "13-11-2025-f-lechno-wasiutynski-n-cox"
    matching = [r for r in recent if r.get("slug", "").strip() == target_slug]
    
    print(f"\nЗаписей с slug '{target_slug}': {len(matching)}")
    if matching:
        print("\nВсе записи этого матча:")
        for i, r in enumerate(matching, 1):
            print(f"  {i}. {r.get('timestamp_msk')} | {r.get('sport')} | message_id: {r.get('telegram_message_id')}")
    
    print("\nПоследние 10 записей:")
    for i, r in enumerate(recent[-10:], 1):
        slug = r.get("slug", "")[:50]
        print(f"  {i}. {r.get('timestamp_msk')} | {r.get('sport')} | {slug}")

