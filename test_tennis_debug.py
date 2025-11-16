#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_tennis_analyzer import analyze_live_tennis_matches
from scores24_graphql_client import fetch_live_matches, fetch_match_stats

print("Проверка тенниса:")
print("=" * 60)

# Получаем все лайв матчи
all_tennis = fetch_live_matches(limit=10, sport="tennis")
print(f"Всего лайв матчей: {len(all_tennis)}")

if len(all_tennis) == 0:
    print("Нет лайв матчей")
    exit(0)

# Берем первые 3 матча для детального анализа
for i, match_info in enumerate(all_tennis[:3], 1):
    print(f"\n{i}. Матч {i}:")
    slug = match_info.get('slug')
    teams = match_info.get('teams', [])
    if len(teams) >= 2:
        print(f"   {teams[0].get('name', 'N/A')} vs {teams[1].get('name', 'N/A')}")
    
    try:
        details = fetch_match_stats(slug, sport="tennis")
        tournament_name = (
            (details.get("unique_tournament") or {}).get("name")
            or details.get("tournament_name")
            or match_info.get("tournament_name")
            or match_info.get("category_name")
        )
        print(f"   Турнир: {tournament_name}")
        print(f"   Счет: {details.get('result_score')}")
        print(f"   Статус: {(details.get('status') or {}).get('code')}")
        
        result_scores = details.get("result_scores") or []
        print(f"   Сеты: {len(result_scores)}")
        for score in result_scores[:3]:
            print(f"     {score}")
    except Exception as e:
        print(f"   Ошибка: {e}")

print("\n" + "=" * 60)
print("Анализ через analyze_live_tennis_matches:")
analyzed = analyze_live_tennis_matches(limit=10)
print(f"Прошло анализ: {len(analyzed)} матчей")

if len(analyzed) > 0:
    print("\nПервый прошедший матч:")
    m = analyzed[0]
    print(f"  {m.get('home_player')} vs {m.get('away_player')}")
    print(f"  Счет: {m.get('sets_home')}:{m.get('sets_away')}")
    print(f"  Текущий сет: {m.get('current_set_index')}, геймы: {m.get('games_home')}:{m.get('games_away')}")

