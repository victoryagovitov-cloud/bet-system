#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

log_file = Path("data/recommendations_log.csv")
if not log_file.exists():
    print("Лог файл не существует")
    exit(0)

rows = list(csv.DictReader(open(log_file, encoding="utf-8")))
print(f"Всего записей: {len(rows)}")
print("\nПоследние 10 матчей:")
for r in rows[-10:]:
    timestamp = r.get("timestamp_msk", "")
    home = r.get("home_team", "")
    away = r.get("away_team", "")
    score = r.get("score", "")
    slug = r.get("slug", "")
    print(f"{timestamp} | {home} - {away} | {score} | slug: {slug}")

