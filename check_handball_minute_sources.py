#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Проверка всех источников минуты в гандболе"""

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_handball_analyzer import _parse_minute
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 60)
print("ПРОВЕРКА ВСЕХ ИСТОЧНИКОВ МИНУТЫ В ГАНДБОЛЕ")
print("=" * 60)

all_handball = fetch_live_matches(limit=15, sport="handball")

for i, match_info in enumerate(all_handball, 1):
    slug = match_info["slug"]
    teams = match_info.get("teams", [])
    home = teams[0].get("name", "?") if teams else "?"
    away = teams[1].get("name", "?") if len(teams) > 1 else "?"
    
    print(f"\n{i}. {home} vs {away}")
    
    try:
        details = fetch_match_stats(slug, sport="handball")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        continue
    
    # Проверяем ВСЕ возможные источники минуты
    print("   📊 ИСТОЧНИКИ МИНУТЫ:")
    
    minute_match_info = match_info.get("minute")
    minute_details = details.get("minute")
    minute_status = (details.get("status") or {}).get("code")
    
    print(f"      match_info.minute: {minute_match_info} (тип: {type(minute_match_info)})")
    print(f"      details.minute: {minute_details} (тип: {type(minute_details)})")
    print(f"      status.code: {minute_status}")
    
    # Как в анализаторе
    minute_combined = minute_details or minute_match_info
    minute_parsed = _parse_minute(minute_combined)
    print(f"      _parse_minute({minute_combined}): {minute_parsed}")
    
    # Проверяем другие поля
    game_state = details.get("game_state") or {}
    print(f"      game_state: {game_state}")
    
    # Проверяем statistic
    statistic = details.get("statistic")
    if statistic:
        periods = statistic.get("periods", [])
        print(f"      statistic.periods: {len(periods)} периодов")
        for period in periods[:2]:
            print(f"         период {period.get('type')}: {period}")
    
    if minute_parsed:
        print(f"   ✅ Минута найдена: {minute_parsed}")
    else:
        print(f"   ❌ Минута не найдена")

