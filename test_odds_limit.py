#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Тест: сколько матчей проходит с новым лимитом кэф 1.85"""

from graphql_live_analyzer import analyze_live_matches
from generate_live_report import _get_leader_odds, OddsInfo
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 60)
print("ТЕСТ: МАТЧИ С РАЗНЫМИ ЛИМИТАМИ КЭФ")
print("=" * 60)

# Анализируем матчи
matches = analyze_live_matches(limit=100)
print(f"\n📊 Всего матчей с полной статистикой: {len(matches)}\n")

# Проверяем с разными лимитами
limits = [1.72, 1.85, 1.90, 2.00]
results = {}

for limit in limits:
    count = 0
    matches_with_odds = []
    
    for match in matches:
        if match.get("dominance_score", 0) <= 0:
            continue
        
        odds = _get_leader_odds(match["slug"], match["leader_index"])
        if odds.value is None:
            continue
        
        if odds.value <= limit:
            count += 1
            if len(matches_with_odds) < 5:  # Показываем первые 5
                matches_with_odds.append({
                    "teams": match["teams"],
                    "score": match["score"],
                    "minute": match["minute"],
                    "odds": odds.value,
                    "dominance": match.get("dominance_score", 0)
                })
    
    results[limit] = {
        "count": count,
        "examples": matches_with_odds
    }

print("РЕЗУЛЬТАТЫ:\n")
for limit in limits:
    data = results[limit]
    print(f"Кэф ≤ {limit}: {data['count']} матчей")
    if data['examples']:
        print("   Примеры:")
        for ex in data['examples']:
            print(f"      {ex['teams'][0]} vs {ex['teams'][1]} - {ex['score']} ({ex['minute']}') | кэф {ex['odds']:.2f} | dominance {ex['dominance']:.1f}")
    print()

print("=" * 60)
print("РЕКОМЕНДАЦИЯ:")
print("=" * 60)

if results[1.85]['count'] >= 8:
    print(f"✅ Лимит 1.85 дает {results[1.85]['count']} матчей - достаточно для 8-12 прогнозов в день")
elif results[1.90]['count'] >= 8:
    print(f"⚠️  Лимит 1.85 дает {results[1.85]['count']} матчей - мало. Рассмотри 1.90 ({results[1.90]['count']} матчей)")
else:
    print(f"❌ Даже с лимитом 1.90 только {results[1.90]['count']} матчей")
    print("   Нужно ослабить другие критерии (dominance_score, метрики)")

