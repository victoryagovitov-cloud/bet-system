#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Детальная проверка статистики матчей"""

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_live_analyzer import _parse_score, _extract_totals, _parse_minute_value
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 60)
print("ДЕТАЛЬНАЯ ПРОВЕРКА СТАТИСТИКИ МАТЧЕЙ")
print("=" * 60)

all_live = fetch_live_matches(limit=50)
print(f"\n📊 Всего live матчей: {len(all_live)}\n")

# Проверяем матчи с неничейным счетом
nondraw_matches = []

for match_info in all_live:
    slug = match_info["slug"]
    teams = match_info.get("teams", [])
    home = teams[0].get("name", "?") if teams else "?"
    away = teams[1].get("name", "?") if len(teams) > 1 else "?"
    
    try:
        details = fetch_match_stats(slug)
    except Exception as e:
        continue
    
    score = _parse_score(details)
    if not score:
        continue
    home_score, away_score = score
    if home_score == away_score:
        continue
    
    # Это неничейный матч
    minute = details.get("minute") or match_info.get("minute")
    tournament = (
        (details.get("unique_tournament") or {}).get("name")
        or details.get("tournament_name")
        or match_info.get("tournament_name")
        or "?"
    )
    
    nondraw_matches.append({
        "slug": slug,
        "teams": [home, away],
        "score": f"{home_score}:{away_score}",
        "minute": minute,
        "tournament": tournament,
        "details": details
    })

print(f"✅ Неничейных матчей: {len(nondraw_matches)}\n")

# Анализируем статистику каждого
for i, match in enumerate(nondraw_matches[:10], 1):
    print("=" * 60)
    print(f"{i}. {match['teams'][0]} vs {match['teams'][1]}")
    print(f"   Счет: {match['score']} ({match['minute']}')")
    print(f"   Турнир: {match['tournament']}")
    print()
    
    details = match["details"]
    
    # Проверяем статистику
    statistic = details.get("statistic")
    if statistic:
        print("   📊 СТАТИСТИКА:")
        periods = statistic.get("periods", [])
        for period in periods:
            period_type = period.get("type", "?")
            print(f"      Период: {period_type}")
            groups = period.get("groups", [])
            for group in groups:
                group_type = group.get("type", "?")
                print(f"         Группа: {group_type}")
                items = group.get("items", [])
                for item in items:
                    item_type = item.get("type", "?")
                    name = item.get("name", "?")
                    team1 = item.get("team1_value")
                    team2 = item.get("team2_value")
                    print(f"            {item_type} ({name}): {team1} - {team2}")
    else:
        print("   ❌ Статистика отсутствует")
    
    # Проверяем позиции
    standings = details.get("standings", [])
    if standings:
        print("\n   📍 ПОЗИЦИИ В ТАБЛИЦЕ:")
        for standing in standings:
            team = standing.get("team", {}).get("name", "?")
            pos_total = standing.get("position_total")
            pos_home = standing.get("position_home")
            pos_away = standing.get("position_away")
            print(f"      {team}: общая={pos_total}, дома={pos_home}, в гостях={pos_away}")
    else:
        print("\n   ❌ Позиции в таблице отсутствуют")
    
    # Проверяем какие метрики есть через _extract_totals
    totals = _extract_totals(statistic)
    print("\n   🔍 ИЗВЛЕЧЕННЫЕ МЕТРИКИ:")
    if totals:
        for metric_name, (val1, val2) in totals.items():
            print(f"      {metric_name}: {val1} - {val2}")
    else:
        print("      Нет метрик")
    
    # Проверяем требуемые метрики
    xg = totals.get("xg")
    possession = totals.get("ball_possession")
    shots_total = totals.get("shots_total")
    shots_on_target = totals.get("shots_on_target") or totals.get("shots_on_goal")
    
    print("\n   ✅ ПРОВЕРКА ТРЕБУЕМЫХ МЕТРИК:")
    print(f"      xG: {'✅' if xg and xg[0] is not None and xg[1] is not None else '❌'} {xg}")
    print(f"      Владение: {'✅' if possession and possession[0] is not None and possession[1] is not None else '❌'} {possession}")
    print(f"      Удары всего: {'✅' if shots_total and shots_total[0] is not None and shots_total[1] is not None else '❌'} {shots_total}")
    print(f"      Удары в створ: {'✅' if shots_on_target and shots_on_target[0] is not None and shots_on_target[1] is not None else '❌'} {shots_on_target}")
    
    print()

