#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_live_analyzer import analyze_live_matches
from graphql_tennis_analyzer import analyze_live_tennis_matches
from generate_live_report import _get_leader_odds, MIN_ODDS, PRIMARY_MAX_ODDS, EXTENDED_MAX_ODDS, EXTENDED_MIN_DOMINANCE

print("=" * 70)
print("ДИАГНОСТИКА ТЕКУЩЕГО АНАЛИЗА")
print("=" * 70)

# Футбол
print("\nФУТБОЛ:")
football_matches = analyze_live_matches(limit=50)
print(f"Всего live матчей: {len(football_matches)}")

if football_matches:
    print("\nПервые 10 матчей:")
    for i, m in enumerate(football_matches[:10], 1):
        teams = m.get("teams", ["?", "?"])
        score = m.get("score", "?")
        dominance = m.get("dominance_score", 0)
        slug = m.get("slug", "")
        leader_idx = m.get("leader_index", 0)
        odds = _get_leader_odds(slug, leader_idx)
        
        print(f"  {i}. {teams[0]} vs {teams[1]}: {score}")
        print(f"      Dominance: {dominance:.1f}, Кэф: {odds.value if odds.value else 'НЕТ'}")
        
        # Проверка фильтров
        if dominance < -5.0:
            print(f"      [FILTERED] Явный аутсайдер (dominance < -5.0)")
        elif odds.value is None:
            print(f"      [FILTERED] Нет коэффициента")
        elif odds.value < MIN_ODDS:
            print(f"      [FILTERED] Кэф < {MIN_ODDS}")
        elif odds.value <= PRIMARY_MAX_ODDS:
            leader = m.get("leader_metrics", {})
            trailing = m.get("trailing_metrics", {})
            xg_diff = leader.get("xg", 0) - trailing.get("xg", 0)
            sot_diff = leader.get("shots_on_target", 0) - trailing.get("shots_on_target", 0)
            if dominance > 0 or (xg_diff >= 0 and sot_diff >= 0):
                print(f"      [OK] PRIMARY tier")
            else:
                print(f"      [FILTERED] Не проходит PRIMARY критерии")
        elif odds.value <= EXTENDED_MAX_ODDS:
            leader = m.get("leader_metrics", {})
            trailing = m.get("trailing_metrics", {})
            xg_diff = leader.get("xg", 0) - trailing.get("xg", 0)
            sot_diff = leader.get("shots_on_target", 0) - trailing.get("shots_on_target", 0)
            if (dominance >= EXTENDED_MIN_DOMINANCE or 
                (xg_diff >= 0.1 and sot_diff >= 0) or 
                (dominance > 0 and odds.value >= 1.15)):
                print(f"      [OK] EXTENDED tier")
            else:
                print(f"      [FILTERED] Не проходит EXTENDED критерии")
        else:
            print(f"      [FILTERED] Кэф > {EXTENDED_MAX_ODDS}")

# Теннис
print("\nТЕННИС:")
tennis_matches = analyze_live_tennis_matches(limit=30)
print(f"Всего live матчей: {len(tennis_matches)}")

if tennis_matches:
    print("\nПервые 5 матчей:")
    for i, m in enumerate(tennis_matches[:5], 1):
        teams = m.get("teams", ["?", "?"])
        score = m.get("score", "?")
        dominance = m.get("dominance_score", 0)
        slug = m.get("slug", "")
        leader_idx = m.get("leader_index", 0)
        odds = _get_leader_odds(slug, leader_idx, sport="tennis")
        points_diff = m.get("points_diff", 0)
        
        print(f"  {i}. {teams[0]} vs {teams[1]}: {score}")
        print(f"      Dominance: {dominance:.1f}, Кэф: {odds.value if odds.value else 'НЕТ'}, Points diff: {points_diff}")
        
        if odds.value is None:
            print(f"      [FILTERED] Нет коэффициента")
        elif odds.value < MIN_ODDS:
            print(f"      [FILTERED] Кэф < {MIN_ODDS}")
        elif odds.value <= PRIMARY_MAX_ODDS:
            if dominance > 0 or points_diff > 0:
                print(f"      [OK] PRIMARY tier")
            else:
                print(f"      [FILTERED] Не проходит PRIMARY критерии")
        elif odds.value <= EXTENDED_MAX_ODDS:
            if (dominance >= EXTENDED_MIN_DOMINANCE or 
                points_diff >= 2 or 
                (dominance > 0 and odds.value >= 1.15)):
                print(f"      [OK] EXTENDED tier")
            else:
                print(f"      [FILTERED] Не проходит EXTENDED критерии")
        else:
            print(f"      [FILTERED] Кэф > {EXTENDED_MAX_ODDS}")

print("\n" + "=" * 70)

