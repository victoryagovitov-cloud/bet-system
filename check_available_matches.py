#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_live_analyzer import analyze_live_matches
from graphql_tennis_analyzer import analyze_live_tennis_matches
from graphql_handball_analyzer import analyze_live_handball_matches
from generate_live_report import _get_recent_slugs, _filter_duplicates

print("=" * 60)
print("ПРОВЕРКА ДОСТУПНЫХ МАТЧЕЙ")
print("=" * 60)

# Футбол
print("\n⚽ ФУТБОЛ:")
football_all = analyze_live_matches(limit=120)
print(f"  Всего найдено: {len(football_all)}")
recent_slugs = _get_recent_slugs(hours=4)
football_filtered = _filter_duplicates(football_all, recent_slugs)
print(f"  После дедупликации: {len(football_filtered)}")
if football_filtered:
    print("  Примеры:")
    for m in football_filtered[:3]:
        teams = m.get("teams", [])
        score = m.get("score", "")
        print(f"    - {teams[0] if teams else '?'} - {teams[1] if len(teams) > 1 else '?'} ({score})")

# Теннис
print("\n🎾 ТЕННИС:")
tennis_all = analyze_live_tennis_matches(limit=80)
print(f"  Всего найдено: {len(tennis_all)}")
tennis_filtered = _filter_duplicates(tennis_all, recent_slugs)
print(f"  После дедупликации: {len(tennis_filtered)}")
if tennis_filtered:
    print("  Примеры:")
    for m in tennis_filtered[:3]:
        teams = m.get("teams", [])
        score = m.get("sets_score", "")
        print(f"    - {teams[0] if teams else '?'} - {teams[1] if len(teams) > 1 else '?'} ({score})")

# Гандбол
print("\n🤾 ГАНДБОЛ:")
handball_all = analyze_live_handball_matches(limit=80)
print(f"  Всего найдено: {len(handball_all)}")
handball_filtered = _filter_duplicates(handball_all, recent_slugs)
print(f"  После дедупликации: {len(handball_filtered)}")
if handball_filtered:
    print("  Примеры:")
    for m in handball_filtered[:3]:
        teams = m.get("teams", [])
        score = m.get("score", "")
        print(f"    - {teams[0] if teams else '?'} - {teams[1] if len(teams) > 1 else '?'} ({score})")

print("\n" + "=" * 60)
print(f"Недавно отправленные (за 4 часа): {len(recent_slugs)} матчей")
if recent_slugs:
    print("  Примеры:", list(recent_slugs)[:3])
print("=" * 60)

