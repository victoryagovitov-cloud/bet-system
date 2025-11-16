#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Отладка: как анализатор гандбола находит минуту"""

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_handball_analyzer import analyze_live_handball_matches, _parse_minute
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 60)
print("ОТЛАДКА: КАК АНАЛИЗАТОР ГАНДБОЛА НАХОДИТ МИНУТУ")
print("=" * 60)

# Проверяем через анализатор
analyzed = analyze_live_handball_matches(limit=30)
print(f"\n📊 Анализатор нашел: {len(analyzed)} матчей\n")

if analyzed:
    print("ПРИМЕРЫ НАЙДЕННЫХ МАТЧЕЙ:")
    for i, match in enumerate(analyzed[:5], 1):
        print(f"\n{i}. {match['teams'][0]} vs {match['teams'][1]}")
        print(f"   Счет: {match['score']}")
        print(f"   Минута: {match['minute']} (numeric: {match['minute_numeric']})")
        print(f"   Разница: {match['score_diff']}")
        print(f"   Тотал: {match['total_score']}")
        print(f"   Турнир: {match.get('tournament', '?')}")
else:
    print("❌ Анализатор не нашел матчей")
    print("\nПроверяю вручную первые 5 матчей:\n")
    
    all_handball = fetch_live_matches(limit=10, sport="handball")
    for i, match_info in enumerate(all_handball[:5], 1):
        slug = match_info["slug"]
        teams = match_info.get("teams", [])
        home = teams[0].get("name", "?") if teams else "?"
        away = teams[1].get("name", "?") if len(teams) > 1 else "?"
        
        print(f"{i}. {home} vs {away}")
        try:
            details = fetch_match_stats(slug, sport="handball")
            minute_match = details.get("minute")
            minute_info = match_info.get("minute")
            minute_parsed = _parse_minute(minute_match or minute_info)
            
            print(f"   details.minute: {minute_match}")
            print(f"   match_info.minute: {minute_info}")
            print(f"   _parse_minute(): {minute_parsed}")
            
            # Проверяем альтернативные источники
            status = details.get("status", {})
            print(f"   status: {status}")
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        print()

