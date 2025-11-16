#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches
from graphql_live_analyzer import _is_tournament_allowed, _is_youth_team

print("=" * 60)
print("ДИАГНОСТИКА ФИЛЬТРАЦИИ")
print("=" * 60)

# Получаем все лайв-матчи напрямую
all_matches = fetch_live_matches(limit=120, sport="soccer")

print(f"\nВсего лайв-матчей футбола: {len(all_matches)}")

filtered_by_tournament = 0
filtered_by_youth_team = 0
filtered_by_score = 0
passed = 0

for match in all_matches:
    tournament = match.get("tournament_name") or match.get("category_name") or ""
    teams = match.get("teams", [])
    home_name = teams[0].get("name") if teams and len(teams) > 0 else None
    away_name = teams[1].get("name") if teams and len(teams) > 1 else None
    score = match.get("game_score", "")
    
    # Проверка турнира
    if not _is_tournament_allowed(tournament):
        filtered_by_tournament += 1
        continue
    
    # Проверка молодежных команд
    if _is_youth_team(home_name) or _is_youth_team(away_name):
        filtered_by_youth_team += 1
        continue
    
    # Проверка счета (неничейный)
    if ":" in str(score):
        parts = str(score).split(":")
        try:
            home_score = int(parts[0])
            away_score = int(parts[1])
            if home_score == away_score:
                filtered_by_score += 1
                continue
        except (ValueError, IndexError):
            pass
    
    passed += 1
    if passed <= 5:
        print(f"  [OK] {home_name} - {away_name} ({score}) | {tournament}")

print(f"\nРезультаты фильтрации:")
print(f"  Отфильтровано по турниру: {filtered_by_tournament}")
print(f"  Отфильтровано по молодежке: {filtered_by_youth_team}")
print(f"  Отфильтровано по ничейному счету: {filtered_by_score}")
print(f"  Прошло базовые фильтры: {passed}")

