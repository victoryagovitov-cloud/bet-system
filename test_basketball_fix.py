#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_basketball_analyzer import analyze_live_basketball_matches

print("Тестирование исправления баскетбола...")
matches = analyze_live_basketball_matches(limit=10)
print(f"\nНайдено матчей: {len(matches)}")

if len(matches) > 0:
    print("\nПервые 3 матча:")
    for i, m in enumerate(matches[:3], 1):
        teams = m.get("teams", ["?", "?"])
        score = m.get("score", "?")
        minute = m.get("minute_numeric", "?")
        dominance = m.get("dominance_score", "?")
        print(f"{i}. {teams[0]} - {teams[1]}")
        print(f"   Счет: {score}, Минута: {minute}, Dominance: {dominance:.2f}")
else:
    print("\nМатчи не найдены. Проверяю детально...")
    from debug_basketball_detailed import *
    # Запустим детальную диагностику

