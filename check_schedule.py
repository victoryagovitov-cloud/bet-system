#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from zoneinfo import ZoneInfo

now = datetime.now(ZoneInfo("Europe/Moscow"))
print(f"Текущее время: {now.strftime('%H:%M')} МСК")
print(f"\nСледующие проверки сегодня:")
times = [
    (9,0),(9,20),(9,40),
    (10,0),(10,20),(10,40),
    (11,0),(11,20),(11,40),
    (12,0),(12,20),(12,40),
    (13,0),(13,20),(13,40),
    (14,0),(14,20),(14,40),
    (15,0),(15,20),(15,40),
    (16,0),(16,20),(16,40),
    (17,0),(17,20),(17,40),
    (18,0),(18,20),(18,40),
    (19,0),(19,20),(19,40),
    (20,0),(20,20),(20,40),
    (21,0),(21,20),(21,40),
    (22,0),(22,20),(22,40),
    (23,0),(23,20),
]

next_times = [f"{h:02d}:{m:02d}" for h, m in times if (h, m) > (now.hour, now.minute)]
if next_times:
    print("  " + "\n  ".join(next_times[:5]))
else:
    print("  Сегодня больше проверок не будет")
    print("  Следующая проверка завтра в 09:00")

