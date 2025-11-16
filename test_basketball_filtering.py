#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from generate_live_report import _select_top_basketball_matches

print("=" * 70)
print("ТЕСТ ФИЛЬТРАЦИИ БАСКЕТБОЛА")
print("=" * 70)

matches = _select_top_basketball_matches(limit=10)
print(f"\nНайдено матчей после фильтрации: {len(matches)}")

if matches:
    print("\nПервые 3 матча:")
    for i, m in enumerate(matches[:3], 1):
        teams = m.get("teams", [])
        home = teams[0] if teams else "?"
        away = teams[1] if len(teams) > 1 else "?"
        score = m.get("score", "?")
        minute = m.get("minute", "?")
        dominance = m.get("dominance_score", 0)
        odds = m.get("odds_info")
        odds_value = odds.value if odds and odds.value else None
        print(f"  {i}. {home} vs {away}")
        print(f"     Счет: {score} | Минута: {minute} | Dominance: {dominance:.1f} | Кэф: {odds_value}")
else:
    print("\n[ПРОБЛЕМА] Матчи не прошли фильтры в generate_live_report")

