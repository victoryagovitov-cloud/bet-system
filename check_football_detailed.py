#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_live_analyzer import analyze_live_matches
from generate_live_report import _select_top_matches, _get_leader_odds, _get_recent_slugs, _filter_duplicates

print("=" * 60)
print("ПРОВЕРКА ФУТБОЛА")
print("=" * 60)

# Шаг 1: Все live матчи
all_matches = analyze_live_matches(limit=100)
print(f"\n1. Всего live матчей: {len(all_matches)}")

if all_matches:
    print("\nПервые 15 матчей:")
    for i, m in enumerate(all_matches[:15], 1):
        teams = m.get("teams", ["?", "?"])
        score = m.get("score", "?")
        dominance = m.get("dominance_score", 0)
        print(f"  {i}. {teams[0]} vs {teams[1]}: {score} (dominance: {dominance:.1f})")

# Шаг 2: После фильтрации по dominance
dominance_filtered = [m for m in all_matches if m.get("dominance_score", 0) > 0]
print(f"\n2. После фильтра по dominance > 0: {len(dominance_filtered)} матчей")

# Шаг 3: Проверка коэффициентов
odds_ok = []
odds_missing = []
odds_too_high = []

for m in dominance_filtered[:20]:
    slug = m.get("slug", "")
    leader_idx = m.get("leader_index", 0)
    odds = _get_leader_odds(slug, leader_idx)
    
    if odds.value is None:
        odds_missing.append(m)
    elif odds.value > 2.00:
        odds_too_high.append(m)
    else:
        odds_ok.append(m)

print(f"\n3. Проверка коэффициентов:")
print(f"  - Кэф подходит (<= 2.00): {len(odds_ok)}")
print(f"  - Нет коэффициентов: {len(odds_missing)}")
print(f"  - Кэф слишком высокий (> 2.00): {len(odds_too_high)}")

if odds_ok:
    print(f"\nМатчи с подходящими коэффициентами:")
    for i, m in enumerate(odds_ok[:10], 1):
        teams = m.get("teams", ["?", "?"])
        score = m.get("score", "?")
        dominance = m.get("dominance_score", 0)
        slug = m.get("slug", "")
        leader_idx = m.get("leader_index", 0)
        odds = _get_leader_odds(slug, leader_idx)
        print(f"  {i}. {teams[0]} vs {teams[1]}: {score}")
        print(f"      Кэф: {odds.value:.2f}, dominance: {dominance:.1f}")

# Шаг 4: Через _select_top_matches
selected = _select_top_matches(limit=10)
print(f"\n4. После _select_top_matches (limit=10): {len(selected)} матчей")

if selected:
    print("\nОтобранные матчи:")
    for i, m in enumerate(selected, 1):
        teams = m.get("teams", ["?", "?"])
        odds_info = m.get("odds_info")
        dominance = m.get("dominance_score", 0)
        print(f"  {i}. {teams[0]} vs {teams[1]}: кэф {odds_info.value if odds_info else '?'}, dominance {dominance:.1f}")

# Шаг 5: Дедупликация
recent_slugs = _get_recent_slugs(4)
print(f"\n5. Дедупликация:")
print(f"  - Недавно отправленные (за 4 часа): {len(recent_slugs)} матчей")
filtered = _filter_duplicates(selected, recent_slugs)
print(f"  - После дедупликации: {len(filtered)} матчей")

if len(selected) > len(filtered):
    print(f"\n  Отфильтровано дедупликацией: {len(selected) - len(filtered)} матчей")
    for m in selected:
        slug = m.get("slug", "")
        if slug in recent_slugs:
            teams = m.get("teams", ["?", "?"])
            print(f"    - {teams[0]} vs {teams[1]} ({slug})")

