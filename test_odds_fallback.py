#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_live_analyzer import analyze_live_matches
from generate_live_report import _get_leader_odds

print("=" * 70)
print("ТЕСТ: ИСПОЛЬЗОВАНИЕ КОЭФФИЦИЕНТОВ ОТ ЛЮБЫХ БУКМЕКЕРОВ")
print("=" * 70)

matches = analyze_live_matches(limit=10)
print(f"\nНайдено матчей: {len(matches)}")

if matches:
    print("\nПроверка коэффициентов:")
    for i, m in enumerate(matches[:5], 1):
        teams = m.get("teams", ["?", "?"])
        slug = m.get("slug", "")
        leader_idx = m.get("leader_index", 0)
        
        odds = _get_leader_odds(slug, leader_idx)
        
        print(f"\n{i}. {teams[0]} vs {teams[1]}")
        print(f"   Slug: {slug}")
        if odds.value:
            print(f"   [OK] Кэф: {odds.value:.2f}, Букмекер: {odds.bookmaker or 'Unknown'}")
        else:
            print(f"   [FAIL] Нет коэффициента")

print("\n" + "=" * 70)
print("ЛОГИКА:")
print("1. Приоритет: BetBoom (если есть)")
print("2. Fallback: любой другой букмекер (если BetBoom нет)")
print("3. Результат: используется любой доступный коэффициент")
print("=" * 70)

