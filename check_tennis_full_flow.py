#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_tennis_analyzer import analyze_live_tennis_matches
from generate_live_report import _select_top_tennis_matches, _get_leader_odds

print("=" * 60)
print("ПОЛНАЯ ПРОВЕРКА ТЕННИСА")
print("=" * 60)

# Шаг 1: analyze_live_tennis_matches
analyzed = analyze_live_tennis_matches(limit=50)
print(f"\n1. После analyze_live_tennis_matches: {len(analyzed)} матчей")

if analyzed:
    print("\nПервые 5 матчей:")
    for i, m in enumerate(analyzed[:5], 1):
        teams = m.get("teams", ["?", "?"])
        sets = m.get("sets_score", "?")
        dominance = m.get("dominance_score", 0)
        print(f"  {i}. {teams[0]} vs {teams[1]}: {sets} (dominance: {dominance:.1f})")
        
        # Проверяем коэффициенты
        slug = m.get("slug", "")
        leader_idx = m.get("leader_index", 0)
        odds = _get_leader_odds(slug, leader_idx, sport="tennis")
        print(f"      Кэф: {odds.value if odds.value else 'НЕТ'}")
        
        if odds.value is None:
            print(f"      [FILTERED] Нет коэффициентов")
        elif odds.value > 2.00:
            print(f"      [FILTERED] Кэф слишком высокий: {odds.value:.2f}")
        else:
            print(f"      [OK] Кэф подходит: {odds.value:.2f}")
else:
    print("\n❌ Нет матчей после analyze_live_tennis_matches!")

# Шаг 2: _select_top_tennis_matches
selected = _select_top_tennis_matches(limit=5)
print(f"\n2. После _select_top_tennis_matches: {len(selected)} матчей")

if selected:
    print("\nОтобранные матчи:")
    for i, m in enumerate(selected, 1):
        teams = m.get("teams", ["?", "?"])
        odds_info = m.get("odds_info")
        print(f"  {i}. {teams[0]} vs {teams[1]}: кэф {odds_info.value if odds_info else '?'}")
else:
    print("\n❌ Нет матчей после _select_top_tennis_matches!")

