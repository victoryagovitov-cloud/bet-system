#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_tennis_analyzer import _parse_pair, _current_set_info, _is_allowed_tennis_tournament

print("=" * 60)
print("ДЕТАЛЬНАЯ ДИАГНОСТИКА ТЕННИСА")
print("=" * 60)

all_matches = fetch_live_matches(limit=20, sport="tennis")
print(f"Всего лайв-матчей: {len(all_matches)}\n")

filtered_no_stats = 0
filtered_no_score = 0
filtered_equal_score = 0
filtered_no_advantage = 0
filtered_no_points = 0
passed = 0

for i, match_info in enumerate(all_matches[:5]):  # Проверяем первые 5
    slug = match_info["slug"]
    teams = match_info.get("teams", [])
    home_name = teams[0].get("name") if teams and len(teams) > 0 else "?"
    away_name = teams[1].get("name") if teams and len(teams) > 1 else "?"
    
    print(f"{i+1}. {home_name} - {away_name}")
    print(f"   Slug: {slug}")
    
    try:
        details = fetch_match_stats(slug, sport="tennis")
    except Exception as e:
        print(f"   [ОШИБКА получения статистики: {e}]")
        filtered_no_stats += 1
        print()
        continue
    
    # Проверка счета
    result_score = _parse_pair(details.get("result_score"))
    sets_home = result_score[0] if result_score else 0
    sets_away = result_score[1] if result_score else 0
    
    result_scores = details.get("result_scores") or []
    current_set_index, current_games = _current_set_info(result_scores)
    games_home, games_away = current_games
    
    if not result_score and not result_scores:
        print(f"   [ОТФИЛЬТРОВАН - нет счета]")
        filtered_no_score += 1
        print()
        continue
    
    set_diff = sets_home - sets_away
    game_diff = games_home - games_away
    
    print(f"   Счет сетов: {sets_home}:{sets_away}")
    print(f"   Текущие геймы: {games_home}:{games_away} (сет {current_set_index})")
    print(f"   Разница сетов: {set_diff}, разница геймов: {game_diff}")
    
    # Проверка преимущества
    if abs(set_diff) == 0 and abs(game_diff) < 3:
        print(f"   [ОТФИЛЬТРОВАН - недостаточное преимущество]")
        filtered_no_advantage += 1
        print()
        continue
    
    # Проверка статистики
    stats_map = details.get("statistic") or {}
    points = stats_map.get("points_won")
    
    if points and not (points[0] is None or points[1] is None):
        points_diff = points[0] - points[1]
        print(f"   Points won: {points[0]} - {points[1]} (разница: {points_diff})")
        if points_diff < 4:
            print(f"   [ОТФИЛЬТРОВАН - разница points < 4]")
            filtered_no_points += 1
            print()
            continue
    else:
        print(f"   Points won: отсутствует")
        # Если нет points, но есть преимущество в счете - пропускаем
    
    print(f"   [OK - прошел базовые проверки]")
    passed += 1
    print()

print(f"\nИтоги:")
print(f"  Ошибка получения статистики: {filtered_no_stats}")
print(f"  Нет счета: {filtered_no_score}")
print(f"  Недостаточное преимущество: {filtered_no_advantage}")
print(f"  Разница points < 4: {filtered_no_points}")
print(f"  Прошло базовые проверки: {passed}")
