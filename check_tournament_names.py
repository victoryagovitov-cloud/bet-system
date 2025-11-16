#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats

print("=" * 60)
print("ПРОВЕРКА НАЗВАНИЙ ТУРНИРОВ")
print("=" * 60)

matches = fetch_live_matches(limit=20, sport="tennis")
print(f"\nВсего live матчей: {len(matches)}")

tournaments = {}
for m in matches:
    slug = m.get("slug", "")
    tournament = m.get("tournament_name", "N/A")
    
    # Получаем полное название из статистики
    try:
        details = fetch_match_stats(slug, sport="tennis")
        full_tournament = (
            (details.get("unique_tournament") or {}).get("name")
            or details.get("tournament_name")
            or tournament
        )
        if full_tournament not in tournaments:
            tournaments[full_tournament] = []
        tournaments[full_tournament].append(f"{m.get('home_name', '?')} vs {m.get('away_name', '?')}")
    except:
        if tournament not in tournaments:
            tournaments[tournament] = []
        tournaments[tournament].append(f"{m.get('home_name', '?')} vs {m.get('away_name', '?')}")

print(f"\nНайдено уникальных турниров: {len(tournaments)}")
for tournament, matches_list in sorted(tournaments.items()):
    print(f"\n'{tournament}' ({len(matches_list)} матчей):")
    for match in matches_list[:3]:
        print(f"  - {match}")

