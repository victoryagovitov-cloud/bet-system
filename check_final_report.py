#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from generate_live_report import generate_live_report

print("=" * 70)
print("ПРОВЕРКА ФИНАЛЬНОГО ОТЧЕТА")
print("=" * 70)

result = generate_live_report()
# generate_live_report возвращает tuple (report, selected_matches, context)
if isinstance(result, tuple) and len(result) == 3:
    report, matches, context = result
else:
    matches = []

print(f"\nВсего матчей в отчете: {len(matches)}")

sports = {}
for m in matches:
    sport = m.get("sport", "unknown")
    sports[sport] = sports.get(sport, 0) + 1

print("\nПо видам спорта:")
for sport, count in sports.items():
    print(f"  {sport}: {count}")

basketball = [m for m in matches if m.get("sport") == "basketball"]
print(f"\nБаскетбольных матчей: {len(basketball)}")

if basketball:
    print("\nПервые 3 матча:")
    for i, m in enumerate(basketball[:3], 1):
        teams = m.get("teams", [])
        home = teams[0] if teams else "?"
        away = teams[1] if len(teams) > 1 else "?"
        score = m.get("score", "?")
        minute = m.get("minute", "?")
        odds = m.get("odds_info")
        odds_value = odds.value if odds and odds.value else "?"
        print(f"  {i}. {home} vs {away}")
        print(f"     Счет: {score} | Минута: {minute} | Кэф: {odds_value}")

