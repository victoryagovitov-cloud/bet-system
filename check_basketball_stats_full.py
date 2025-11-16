#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
import json

print("=" * 70)
print("ПОЛНАЯ ПРОВЕРКА СТАТИСТИКИ В БАСКЕТБОЛЕ")
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
        print("Нет статистики")
        exit(0)
    
    periods = statistic.get("periods") or []
    print(f"\nПериодов: {len(periods)}")
    
    # Собираем все типы статистики
    all_types = set()
    for period in periods:
        if period.get("type") == "total":
            groups = period.get("groups") or []
            for group in groups:
                items = group.get("items") or []
                for item in items:
                    stat_type = item.get("type")
                    if stat_type:
                        all_types.add(stat_type)
    
    print(f"\nВсе типы статистики ({len(all_types)}):")
    for stat_type in sorted(all_types):
        print(f"  - {stat_type}")
    
    # Ищем очки
    print("\nПоиск поля с очками:")
    for period in periods:
        if period.get("type") == "total":
            groups = period.get("groups") or []
            for group in groups:
                items = group.get("items") or []
                for item in items:
                    stat_type = item.get("type", "").lower()
                    if "point" in stat_type or "score" in stat_type or "очк" in stat_type:
                        print(f"  Найдено: {item.get('type')} = {item.get('team1_value')} - {item.get('team2_value')}")
    
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()

