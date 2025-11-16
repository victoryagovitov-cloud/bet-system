#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import csv

# Проверяем дедупликацию
log_file = Path('data/recommendations_log.csv')
now = datetime.now(ZoneInfo('Europe/Moscow'))
cutoff = now - timedelta(hours=4)

print(f"Текущее время: {now.strftime('%H:%M')} МСК")
print(f"Отсечка (4 часа назад): {cutoff.strftime('%H:%M')} МСК")
print()

if not log_file.exists():
    print("Лог файл не существует - дедупликация не применяется")
else:
    recent_slugs = set()
    with open(log_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp_str = row.get("timestamp_msk", "")
            if not timestamp_str:
                continue
            try:
                row_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                row_time = row_time.replace(tzinfo=ZoneInfo("Europe/Moscow"))
                if row_time >= cutoff:
                    slug = row.get("slug", "").strip()
                    if slug:
                        recent_slugs.add(slug)
            except (ValueError, TypeError):
                continue
    
    print(f"Slug в последние 4 часа: {len(recent_slugs)}")
    if recent_slugs:
        print("\nПоследние 10 slug:")
        for slug in sorted(list(recent_slugs))[-10:]:
            print(f"  - {slug}")
    else:
        print("Нет slug в последние 4 часа - дедупликация не должна фильтровать матчи")

