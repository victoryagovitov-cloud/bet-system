#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Анализ: почему матчи не проходят фильтры"""

from graphql_live_analyzer import analyze_live_matches
from generate_live_report import _get_leader_odds, PRIMARY_MAX_ODDS, EXTENDED_MAX_ODDS, EXTENDED_MIN_DOMINANCE
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 60)
print("АНАЛИЗ ФИЛЬТРАЦИИ МАТЧЕЙ")
print("=" * 60)

matches = analyze_live_matches(limit=100)
print(f"\n📊 Всего матчей с полной статистикой: {len(matches)}\n")

reasons = {
    "dominance_negative": 0,
    "no_odds": 0,
    "odds_too_high_primary": 0,
    "odds_too_high_extended": 0,
    "passed": 0
}

examples = {
    "dominance_negative": [],
    "no_odds": [],
    "odds_too_high_primary": [],
    "odds_too_high_extended": [],
    "passed": []
}

for match in matches:
    dominance = match.get("dominance_score", 0)
    
    # Проверка 1: dominance_score
    if dominance <= 0:
        reasons["dominance_negative"] += 1
        if len(examples["dominance_negative"]) < 3:
            examples["dominance_negative"].append({
                "teams": match["teams"],
                "score": match["score"],
                "dominance": dominance
            })
        continue
    
    # Проверка 2: коэффициенты
    odds = _get_leader_odds(match["slug"], match["leader_index"])
    if odds.value is None:
        reasons["no_odds"] += 1
        if len(examples["no_odds"]) < 3:
            examples["no_odds"].append({
                "teams": match["teams"],
                "score": match["score"],
                "dominance": dominance
            })
        continue
    
    # Проверка 3: лимит кэф
    if odds.value <= PRIMARY_MAX_ODDS:
        reasons["passed"] += 1
        if len(examples["passed"]) < 5:
            examples["passed"].append({
                "teams": match["teams"],
                "score": match["score"],
                "odds": odds.value,
                "dominance": dominance
            })
    elif odds.value <= EXTENDED_MAX_ODDS and dominance >= EXTENDED_MIN_DOMINANCE:
        reasons["passed"] += 1
        if len(examples["passed"]) < 5:
            examples["passed"].append({
                "teams": match["teams"],
                "score": match["score"],
                "odds": odds.value,
                "dominance": dominance,
                "extended": True
            })
    elif odds.value <= EXTENDED_MAX_ODDS:
        reasons["odds_too_high_extended"] += 1
        if len(examples["odds_too_high_extended"]) < 3:
            examples["odds_too_high_extended"].append({
                "teams": match["teams"],
                "score": match["score"],
                "odds": odds.value,
                "dominance": dominance,
                "needed_dominance": EXTENDED_MIN_DOMINANCE
            })
    else:
        reasons["odds_too_high_primary"] += 1
        if len(examples["odds_too_high_primary"]) < 3:
            examples["odds_too_high_extended"].append({
                "teams": match["teams"],
                "score": match["score"],
                "odds": odds.value,
                "dominance": dominance
            })

print("ПРИЧИНЫ ОТСЕВА:\n")
print(f"✅ Прошли фильтры: {reasons['passed']}")
print(f"❌ Отрицательный dominance_score: {reasons['dominance_negative']}")
print(f"❌ Нет коэффициентов: {reasons['no_odds']}")
print(f"⚠️  Кэф > {PRIMARY_MAX_ODDS}, но < {EXTENDED_MAX_ODDS} и dominance < {EXTENDED_MIN_DOMINANCE}: {reasons['odds_too_high_extended']}")
print(f"❌ Кэф > {EXTENDED_MAX_ODDS}: {reasons['odds_too_high_primary']}")

print("\n" + "=" * 60)
print("ПРИМЕРЫ ПРОШЕДШИХ МАТЧЕЙ:")
print("=" * 60)
for ex in examples["passed"]:
    ext = " (extended)" if ex.get("extended") else ""
    print(f"  {ex['teams'][0]} vs {ex['teams'][1]} - {ex['score']} | кэф {ex['odds']:.2f} | dominance {ex['dominance']:.1f}{ext}")

if examples["dominance_negative"]:
    print("\n" + "=" * 60)
    print("ПРИМЕРЫ: ОТРИЦАТЕЛЬНЫЙ DOMINANCE")
    print("=" * 60)
    for ex in examples["dominance_negative"][:3]:
        print(f"  {ex['teams'][0]} vs {ex['teams'][1]} - {ex['score']} | dominance {ex['dominance']:.1f}")

if examples["odds_too_high_extended"]:
    print("\n" + "=" * 60)
    print("ПРИМЕРЫ: КЭФ ВЫСОКИЙ, НО DOMINANCE МАЛО")
    print("=" * 60)
    for ex in examples["odds_too_high_extended"][:3]:
        needed = ex.get("needed_dominance", EXTENDED_MIN_DOMINANCE)
        print(f"  {ex['teams'][0]} vs {ex['teams'][1]} - {ex['score']} | кэф {ex['odds']:.2f} | dominance {ex['dominance']:.1f} (нужно ≥{needed})")

print("\n" + "=" * 60)
print("РЕКОМЕНДАЦИИ:")
print("=" * 60)

if reasons["dominance_negative"] > 0:
    print(f"1. Отрицательный dominance: {reasons['dominance_negative']} матчей")
    print("   → Рассмотри снижение требования dominance_score > 0 до >= -2")
    
if reasons["odds_too_high_extended"] > 0:
    print(f"2. Кэф в диапазоне extended, но низкий dominance: {reasons['odds_too_high_extended']} матчей")
    print(f"   → Снизь EXTENDED_MIN_DOMINANCE с {EXTENDED_MIN_DOMINANCE} до 5.0")

if reasons["passed"] < 8:
    print(f"3. Прошло только {reasons['passed']} матчей - нужно минимум 8")
    print("   → Комбинация: снизить dominance threshold + увеличить extended диапазон")

