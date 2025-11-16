#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Проверка тенниса"""

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_tennis_analyzer import analyze_live_tennis_matches
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 60)
print("ПРОВЕРКА ТЕННИСА")
print("=" * 60)

all_tennis = fetch_live_matches(limit=30, sport="tennis")
print(f"\nВсего live матчей: {len(all_tennis)}")

# Проверяем первые 5 матчей
for i, match_info in enumerate(all_tennis[:5], 1):
    slug = match_info["slug"]
    teams = match_info.get("teams", [])
    home = teams[0].get("name", "?") if teams else "?"
    away = teams[1].get("name", "?") if len(teams) > 1 else "?"
    
    print(f"\n{i}. {home} vs {away}")
    
    try:
        details = fetch_match_stats(slug, sport="tennis")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        continue
    
    print(f"  Статус: {details.get('status', {}).get('code')}")
    print(f"  Счет: {details.get('result_score')}")
    print(f"  result_scores: {details.get('result_scores')}")

analyzed = analyze_live_tennis_matches(limit=30)
print(f"\n\nПрошли analyze_live_tennis_matches: {len(analyzed)}")

if analyzed:
    print("\nПримеры:")
    for m in analyzed[:3]:
        print(f"  {m['teams'][0]} vs {m['teams'][1]} - {m.get('sets_score', '?')}")

