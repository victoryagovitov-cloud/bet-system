#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches
from graphql_tennis_analyzer import _is_allowed_tennis_tournament

print("=" * 60)
print("ДИАГНОСТИКА ТЕННИСА")
print("=" * 60)

# Получаем все лайв-матчи тенниса
all_matches = fetch_live_matches(limit=120, sport="tennis")

print(f"\nВсего лайв-матчей тенниса: {len(all_matches)}")

if len(all_matches) == 0:
    print("\nНЕТ ЛАЙВ-МАТЧЕЙ ТЕННИСА В ДАННЫЙ МОМЕНТ")
    exit(0)

filtered_by_tournament = 0
passed_tournament = 0

print("\nПримеры матчей:")
for i, match in enumerate(all_matches[:10]):
    teams = match.get("teams", [])
    home_name = teams[0].get("name") if teams and len(teams) > 0 else "?"
    away_name = teams[1].get("name") if teams and len(teams) > 1 else "?"
    tournament = match.get("tournament_name") or match.get("category_name") or "N/A"
    score = match.get("game_score", "")
    
    print(f"  {i+1}. {home_name} - {away_name}")
    print(f"     Турнир: {tournament}")
    print(f"     Счет: {score}")
    
    # Проверка турнира
    if tournament and tournament.strip().upper() not in ("N/A", ""):
        if not _is_allowed_tennis_tournament(tournament):
            filtered_by_tournament += 1
            print(f"     [ОТФИЛЬТРОВАН - турнир не разрешен]")
        else:
            passed_tournament += 1
            print(f"     [OK - турнир разрешен]")
    else:
        passed_tournament += 1
        print(f"     [OK - турнир N/A, пропускаем проверку]")
    print()

print(f"\nРезультаты фильтрации по турнирам:")
print(f"  Отфильтровано: {filtered_by_tournament}")
print(f"  Прошло: {passed_tournament}")

# Теперь проверим полный анализ
print("\n" + "=" * 60)
print("ПОЛНЫЙ АНАЛИЗ (analyze_live_tennis_matches):")
print("=" * 60)

from graphql_tennis_analyzer import analyze_live_tennis_matches

analyzed = analyze_live_tennis_matches(limit=80)
print(f"Найдено после полного анализа: {len(analyzed)}")

if analyzed:
    print("\nПримеры найденных матчей:")
    for i, m in enumerate(analyzed[:5]):
        teams = m.get("teams", [])
        print(f"  {i+1}. {teams[0] if teams else '?'} - {teams[1] if len(teams) > 1 else '?'}")
        print(f"     Счет: {m.get('sets_score', '?')}")
        print(f"     Доминирование: {m.get('dominance_score', 0):.2f}")
else:
    print("\nМатчи не прошли полный анализ. Возможные причины:")
    print("  - Недостаточное преимущество в счете")
    print("  - Нет статистики (points_won, breaks)")
    print("  - Коэффициенты слишком высокие")
    print("  - Недостаточное доминирование")
