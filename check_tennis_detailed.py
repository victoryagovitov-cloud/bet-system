#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_tennis_analyzer import _parse_pair, _current_set_info, _is_set_finished

print("=" * 60)
print("ДЕТАЛЬНАЯ ПРОВЕРКА ТЕННИСА")
print("=" * 60)

all_matches = fetch_live_matches(limit=20, sport="tennis")
print(f"\nВсего live матчей: {len(all_matches)}")

passed = 0
filtered = 0

for i, match_info in enumerate(all_matches[:10], 1):
    slug = match_info.get("slug", "?")
    home = match_info.get("home_name", "?")
    away = match_info.get("away_name", "?")
    
    print(f"\n{i}. {home} vs {away}")
    print(f"   Slug: {slug}")
    
    try:
        details = fetch_match_stats(slug, sport="tennis")
    except Exception as e:
        print(f"   [SKIP] Ошибка получения статистики: {e}")
        filtered += 1
        continue
    
    # Проверка статуса
    status_code = (details.get("status") or {}).get("code")
    if status_code in {"100", "110"}:
        print(f"   [FILTERED] Матч завершен или приостановлен (status: {status_code})")
        filtered += 1
        continue
    
    # Проверка сетов
    result_score = _parse_pair(details.get("result_score"))
    sets_home = result_score[0] if result_score else 0
    sets_away = result_score[1] if result_score else 0
    set_diff = sets_home - sets_away
    
    result_scores = details.get("result_scores") or []
    current_set_index, current_games = _current_set_info(result_scores)
    games_home, games_away = current_games
    game_diff = games_home - games_away
    
    print(f"   Сеты: {sets_home}:{sets_away} (разница: {set_diff})")
    print(f"   Текущий сет: {current_set_index}, геймы: {games_home}:{games_away} (разница: {game_diff})")
    
    # Проверка критериев
    leader_index = None
    if set_diff > 0:
        leader_index = 0
    elif set_diff < 0:
        leader_index = 1
    elif game_diff > 0:
        leader_index = 0
    elif game_diff < 0:
        leader_index = 1
    
    if leader_index is None:
        print(f"   [FILTERED] Нет лидера (сеты равны, геймы равны)")
        filtered += 1
        continue
    
    # Проверка раннего матча
    total_games_played = sum(sum(_parse_pair(entry.get("value")) or (0, 0)) for entry in result_scores)
    if total_games_played < 6 and max(sets_home, sets_away) == 0:
        if abs(game_diff) < 3:
            print(f"   [FILTERED] Слишком рано (игр: {total_games_played}, разница геймов: {abs(game_diff)})")
            filtered += 1
            continue
    
    print(f"   [OK] Проходит фильтры!")
    passed += 1

print(f"\n" + "=" * 60)
print(f"ИТОГО: прошло {passed}, отфильтровано {filtered}")

