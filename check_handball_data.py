#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Проверка всех данных гандбольного матча"""

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 60)
print("ПРОВЕРКА ДАННЫХ ГАНДБОЛЬНОГО МАТЧА")
print("=" * 60)

all_handball = fetch_live_matches(limit=5, sport="handball")

for i, match_info in enumerate(all_handball[:3], 1):
    slug = match_info["slug"]
    teams = match_info.get("teams", [])
    home = teams[0].get("name", "?") if teams else "?"
    away = teams[1].get("name", "?") if len(teams) > 1 else "?"
    
    print(f"\n{i}. {home} vs {away}")
    print("-" * 60)
    
    try:
        details = fetch_match_stats(slug, sport="handball")
    except Exception as e:
        print(f"Ошибка: {e}")
        continue
    
    # Проверяем все возможные поля
    print("ВСЕ ПОЛЯ В details:")
    for key in sorted(details.keys()):
        value = details[key]
        if isinstance(value, (dict, list)):
            print(f"  {key}: {type(value).__name__} (len={len(value) if isinstance(value, (list, dict)) else 'N/A'})")
        else:
            print(f"  {key}: {value}")
    
    print("\nДЕТАЛЬНО:")
    print(f"  minute: {details.get('minute')}")
    print(f"  status: {details.get('status')}")
    print(f"  game_state: {details.get('game_state')}")
    print(f"  result_score: {details.get('result_score')}")
    print(f"  game_score: {details.get('game_score')}")
    
    # Проверяем statistic
    statistic = details.get("statistic")
    if statistic:
        print(f"  statistic.periods: {statistic.get('periods')}")
        if statistic.get("periods"):
            for period in statistic["periods"]:
                print(f"    период: {period.get('type')}")

