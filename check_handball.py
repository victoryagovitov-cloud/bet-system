#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches
from graphql_handball_analyzer import analyze_live_handball_matches

print("=" * 60)
print("ПРОВЕРКА ГАНДБОЛА")
print("=" * 60)

# Проверяем raw матчи
print("\n1. Live матчи на Scores24:")
raw_matches = fetch_live_matches(limit=20, sport="handball")
print(f"   Найдено: {len(raw_matches)} матчей")

if raw_matches:
    print("\n   Первые 5 матчей:")
    for i, m in enumerate(raw_matches[:5], 1):
        teams = m.get("teams", [])
        home = teams[0].get("name", "?") if teams else "?"
        away = teams[1].get("name", "?") if len(teams) > 1 else "?"
        tournament = m.get("tournament_name", "?")
        print(f"   {i}. {tournament}: {home} vs {away}")

# Проверяем проанализированные матчи
print("\n2. Проанализированные матчи:")
analyzed = analyze_live_handball_matches(limit=20)
print(f"   Найдено: {len(analyzed)} матчей")

if analyzed:
    print("\n   Первые 3 матча:")
    for i, m in enumerate(analyzed[:3], 1):
        teams = m.get("teams", [])
        home = teams[0] if teams else "?"
        away = teams[1] if len(teams) > 1 else "?"
        score = m.get("score", "?")
        minute = m.get("minute", "?")
        dominance = m.get("dominance_score", 0)
        print(f"   {i}. {home} vs {away} | {score} ({minute}) | dominance: {dominance:.1f}")
else:
    print("   Матчи не прошли фильтры анализатора")

print("\n" + "=" * 60)

