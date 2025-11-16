#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_live_analyzer import _parse_score, _extract_totals, _extract_positions

print("=" * 60)
print("ПРОВЕРКА ЛОГИКИ ОПРЕДЕЛЕНИЯ ЛИДЕРА")
print("=" * 60)

matches = fetch_live_matches(limit=10, sport="soccer")

for match_info in matches[:3]:
    slug = match_info["slug"]
    teams = match_info.get("teams", [])
    home_name = teams[0].get("name") if teams and len(teams) > 0 else "?"
    away_name = teams[1].get("name") if teams and len(teams) > 1 else "?"
    
    print(f"\n{home_name} - {away_name}")
    print(f"Slug: {slug}")
    
    try:
        details = fetch_match_stats(slug)
    except Exception as e:
        print(f"Ошибка: {e}")
        continue
    
    score = _parse_score(details)
    if not score:
        print("Нет счета")
        continue
    
    home_score, away_score = score
    print(f"Счет: {home_score}:{away_score}")
    
    # Определяем лидера по счету
    if home_score > away_score:
        leader_index = 0
        trailing_index = 1
        print(f"Лидер по счету: {home_name} (домашние)")
    elif away_score > home_score:
        leader_index = 1
        trailing_index = 0
        print(f"Лидер по счету: {away_name} (гости)")
    else:
        print("Равный счет")
        continue
    
    # Получаем статистику
    totals = _extract_totals(details.get("statistic"))
    xg = totals.get("xg")
    possession = totals.get("possession")
    shots_on_target = totals.get("shots_on_target")
    shots_total = totals.get("shots_total")
    
    print(f"\nСтатистика:")
    print(f"  xG: {xg}")
    print(f"  Владение: {possession}")
    print(f"  Удары в створ: {shots_on_target}")
    print(f"  Всего ударов: {shots_total}")
    
    # Проверяем метрики лидера и проигрывающего
    if xg:
        leader_xg = xg[leader_index]
        trailing_xg = xg[trailing_index]
        print(f"\n  xG лидера ({leader_index}): {leader_xg}")
        print(f"  xG проигрывающего ({trailing_index}): {trailing_xg}")
        print(f"  Разница xG: {leader_xg - trailing_xg}")
    
    if possession:
        leader_poss = possession[leader_index]
        trailing_poss = possession[trailing_index]
        print(f"\n  Владение лидера: {leader_poss}%")
        print(f"  Владение проигрывающего: {trailing_poss}%")
        print(f"  Разница владения: {leader_poss - trailing_poss}%")
    
    if shots_on_target:
        leader_sot = shots_on_target[leader_index]
        trailing_sot = shots_on_target[trailing_index]
        print(f"\n  Удары в створ лидера: {leader_sot}")
        print(f"  Удары в створ проигрывающего: {trailing_sot}")
        print(f"  Разница ударов в створ: {leader_sot - trailing_sot}")

