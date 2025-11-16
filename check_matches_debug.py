#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_live_analyzer import analyze_live_matches
from graphql_tennis_analyzer import analyze_live_tennis_matches
from generate_live_report import _select_top_matches, _select_top_tennis_matches, _get_leader_odds

print("=" * 60)
print("ПРОВЕРКА ФУТБОЛА")
print("=" * 60)

# Получаем все матчи
all_football = analyze_live_matches(limit=50)
print(f"\nВсего найдено live матчей: {len(all_football)}")

if all_football:
    print("\nПервые 10 матчей:")
    for i, m in enumerate(all_football[:10], 1):
        teams = m.get("teams", ["?", "?"])
        score = m.get("score", "?")
        dominance = m.get("dominance_score", 0)
        print(f"  {i}. {teams[0]} vs {teams[1]}: {score} (dominance: {dominance:.1f})")
    
    # Проверяем фильтрацию
    print("\n" + "=" * 60)
    print("ПРОВЕРКА ФИЛЬТРОВ")
    print("=" * 60)
    
    filtered_count = 0
    no_dominance = 0
    no_odds = 0
    odds_too_high = 0
    
    for m in all_football[:20]:
        if m.get("dominance_score", 0) <= 0:
            no_dominance += 1
            continue
        
        odds = _get_leader_odds(m["slug"], m["leader_index"])
        if odds.value is None:
            no_odds += 1
            continue
        
        if odds.value > 2.00:
            odds_too_high += 1
            continue
        
        filtered_count += 1
        teams = m.get("teams", ["?", "?"])
        print(f"  ✓ {teams[0]} vs {teams[1]}: кэф {odds.value:.2f}, dominance {m.get('dominance_score', 0):.1f}")
    
    print(f"\nИтого после фильтров: {filtered_count}")
    print(f"  - Нет dominance: {no_dominance}")
    print(f"  - Нет коэффициентов: {no_odds}")
    print(f"  - Коэффициент > 2.00: {odds_too_high}")
else:
    print("Нет live матчей!")

print("\n" + "=" * 60)
print("ПРОВЕРКА ТЕННИСА")
print("=" * 60)

all_tennis = analyze_live_tennis_matches(limit=50)
print(f"\nВсего найдено live матчей: {len(all_tennis)}")

if all_tennis:
    print("\nПервые 10 матчей:")
    for i, m in enumerate(all_tennis[:10], 1):
        teams = m.get("teams", ["?", "?"])
        sets = m.get("sets_score", "?")
        dominance = m.get("dominance_score", 0)
        print(f"  {i}. {teams[0]} vs {teams[1]}: {sets} (dominance: {dominance:.1f})")
    
    # Проверяем фильтрацию
    print("\n" + "=" * 60)
    print("ПРОВЕРКА ФИЛЬТРОВ ТЕННИС")
    print("=" * 60)
    
    filtered_count = 0
    no_odds = 0
    odds_too_high = 0
    
    for m in all_tennis[:20]:
        odds = _get_leader_odds(m["slug"], m["leader_index"], sport="tennis")
        if odds.value is None:
            no_odds += 1
            continue
        
        if odds.value > 2.00:
            odds_too_high += 1
            continue
        
        filtered_count += 1
        teams = m.get("teams", ["?", "?"])
        print(f"  ✓ {teams[0]} vs {teams[1]}: кэф {odds.value:.2f}, dominance {m.get('dominance_score', 0):.1f}")
    
    print(f"\nИтого после фильтров: {filtered_count}")
    print(f"  - Нет коэффициентов: {no_odds}")
    print(f"  - Коэффициент > 2.00: {odds_too_high}")
else:
    print("Нет live матчей!")

print("\n" + "=" * 60)
print("ФИНАЛЬНАЯ ПРОВЕРКА ЧЕРЕЗ _select_top")
print("=" * 60)

football_selected = _select_top_matches(limit=5)
print(f"\nФутбол отобрано: {len(football_selected)}")
for m in football_selected:
    teams = m.get("teams", ["?", "?"])
    print(f"  - {teams[0]} vs {teams[1]}")

tennis_selected = _select_top_tennis_matches(limit=5)
print(f"\nТеннис отобрано: {len(tennis_selected)}")
for m in tennis_selected:
    teams = m.get("teams", ["?", "?"])
    print(f"  - {teams[0]} vs {teams[1]}")

