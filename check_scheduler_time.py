#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from zoneinfo import ZoneInfo

now = datetime.now(ZoneInfo("Europe/Moscow"))
print(f"Текущее время: {now.strftime('%H:%M:%S')} МСК")
print(f"Дата: {now.date()}")

slot_22_00 = now.replace(hour=22, minute=0, second=0, microsecond=0)
delta = (now - slot_22_00).total_seconds()
print(f"\nРазница с 22:00: {delta:.0f} секунд")
print(f"Прошло после 22:00: {delta/60:.1f} минут")

grace_minutes = 7
if delta > grace_minutes * 60:
    print(f"\n[ПРОБЛЕМА] Grace period ({grace_minutes} минут) уже прошел!")
    print("Слот 22:00 пропущен и не будет выполнен.")
else:
    print(f"\n[OK] Grace period еще не прошел, слот должен был сработать")

