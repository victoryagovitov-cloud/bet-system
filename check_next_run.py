#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Расписание проверок (каждые 20 минут)
SCHEDULE_TIMES = [
    (9, 0), (9, 20), (9, 40),
    (10, 0), (10, 20), (10, 40),
    (11, 0), (11, 20), (11, 40),
    (12, 0), (12, 20), (12, 40),
    (13, 0), (13, 20), (13, 40),
    (14, 0), (14, 20), (14, 40),
    (15, 0), (15, 20), (15, 40),
    (16, 0), (16, 20), (16, 40),
    (17, 0), (17, 20), (17, 40),
    (18, 0), (18, 20), (18, 40),
    (19, 0), (19, 20), (19, 40),
    (20, 0), (20, 20), (20, 40),
    (21, 0), (21, 20), (21, 40),
    (22, 0), (22, 20), (22, 40),
    (23, 0), (23, 20),
]

now = datetime.now(ZoneInfo("Europe/Moscow"))
current_time = now.hour * 60 + now.minute

print("=" * 60)
print("РАСПИСАНИЕ ПРОВЕРОК")
print("=" * 60)
print(f"Текущее время: {now.strftime('%H:%M')} МСК")
print(f"Дата: {now.strftime('%d.%m.%Y')}")
print()

# Находим следующую проверку
next_runs = []
for hour, minute in SCHEDULE_TIMES:
    check_time = hour * 60 + minute
    if check_time > current_time:
        next_runs.append((hour, minute))
        if len(next_runs) >= 3:
            break

if next_runs:
    print("Следующие проверки сегодня:")
    for hour, minute in next_runs:
        check_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        time_diff = (check_dt - now).total_seconds() / 60
        print(f"  {hour:02d}:{minute:02d} МСК (через {int(time_diff)} минут)")
else:
    # Если сегодня больше нет проверок, показываем первую завтра
    tomorrow = now + timedelta(days=1)
    first_check = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    time_diff = (first_check - now).total_seconds() / 3600
    print("Сегодня проверок больше нет.")
    print(f"Следующая проверка: {first_check.strftime('%H:%M')} МСК завтра ({first_check.strftime('%d.%m.%Y')})")
    print(f"Через: {int(time_diff)} часов {int((time_diff % 1) * 60)} минут")

print()
print("=" * 60)

