#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
import json

print("=" * 70)
print("ПРОВЕРКА СТАТИСТИКИ В БАСКЕТБОЛЕ")
print("=" * 70)

all_matches = fetch_live_matches(limit=10, sport="basketball")

if len(all_matches) == 0:
    print("Нет матчей")
    exit(0)

# Проверяем первый матч
match_info = all_matches[0]
slug = match_info.get("slug", "")

print(f"\nМатч: {slug}")

try:
    details = fetch_match_stats(slug, sport="basketball")
    
    statistic = details.get("statistic")
    if not statistic:
        print("Нет статистики вообще")
    else:
        print("\nСтруктура statistic:")
        print(f"  Тип: {type(statistic)}")
        
        if isinstance(statistic, dict):
            print(f"  Ключи: {list(statistic.keys())}")
            
            # Проверяем periods
            periods = statistic.get("periods")
            if periods:
                print(f"\n  Периодов: {len(periods)}")
                if len(periods) > 0:
                    first_period = periods[0]
                    print(f"  Первый период: {json.dumps(first_period, indent=4, ensure_ascii=False, default=str)[:500]}")
            
            # Проверяем groups
            groups = statistic.get("groups")
            if groups:
                print(f"\n  Групп: {len(groups)}")
                if len(groups) > 0:
                    first_group = groups[0]
                    print(f"  Первая группа: {json.dumps(first_group, indent=4, ensure_ascii=False, default=str)[:500]}")
            
            # Проверяем totals
            totals = statistic.get("totals")
            if totals:
                print(f"\n  Totals: {json.dumps(totals, indent=4, ensure_ascii=False, default=str)[:500]}")
        else:
            print(f"  Содержимое: {str(statistic)[:500]}")
            
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()

