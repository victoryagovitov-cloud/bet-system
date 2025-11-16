#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Проверка логики анализатора гандбола - как он находит минуту"""

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_handball_analyzer import analyze_live_handball_matches
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 60)
print("ПРОВЕРКА: КАК АНАЛИЗАТОР НАХОДИТ МИНУТУ")
print("=" * 60)

analyzed = analyze_live_handball_matches(limit=30)
print(f"\n📊 Анализатор нашел: {len(analyzed)} матчей\n")

# Проверяем первые 5 найденных матчей
for i, match in enumerate(analyzed[:5], 1):
    slug = match["slug"]
    print(f"{i}. {match['teams'][0]} vs {match['teams'][1]}")
    print(f"   Минута в результате: {match['minute']} (numeric: {match['minute_numeric']})")
    
    # Получаем детали и проверяем, откуда взялась минута
    try:
        details = fetch_match_stats(slug, sport="handball")
        match_info = next((m for m in fetch_live_matches(limit=50, sport="handball") if m["slug"] == slug), None)
        
        minute_details = details.get("minute")
        minute_match_info = match_info.get("minute") if match_info else None
        
        print(f"   details.minute: {minute_details}")
        print(f"   match_info.minute: {minute_match_info}")
        
        # Проверяем statistic.periods - может быть там минута?
        statistic = details.get("statistic")
        if statistic:
            periods = statistic.get("periods", [])
            print(f"   statistic.periods: {len(periods)} периодов")
            for period in periods:
                period_type = period.get("type")
                print(f"      период {period_type}: {json.dumps(period, indent=8, ensure_ascii=False)[:200]}")
        
        # Проверяем result_scores - может быть там время?
        result_scores = details.get("result_scores", [])
        if result_scores:
            print(f"   result_scores: {len(result_scores)} записей")
            for rs in result_scores[:2]:
                print(f"      {rs.get('type')}: {rs.get('value')}")
        
        print()
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}\n")

