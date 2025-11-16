#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_tennis_analyzer import (
    _parse_pair, _current_set_info, _extract_stats, _is_allowed_tennis_tournament
)
import math

print("=" * 60)
print("ПОЧЕМУ МАТЧИ НЕ ПРОХОДЯТ")
print("=" * 60)

all_matches = fetch_live_matches(limit=10, sport="tennis")
print(f"\nВсего live матчей: {len(all_matches)}")

for i, match_info in enumerate(all_matches[:5], 1):
    slug = match_info.get("slug", "?")
    print(f"\n{'='*60}")
    print(f"Матч {i}: {slug}")
    print(f"{'='*60}")
    
    try:
        details = fetch_match_stats(slug, sport="tennis")
    except Exception as e:
        print(f"[SKIP] Ошибка получения статистики: {e}")
        continue
    
    # Проверка турнира
    tournament_name = (
        (details.get("unique_tournament") or {}).get("name")
        or details.get("tournament_name")
        or match_info.get("tournament_name")
        or match_info.get("category_name")
    )
    print(f"Турнир: {tournament_name}")
    if tournament_name and tournament_name.strip().upper() not in ("N/A", ""):
        if not _is_allowed_tennis_tournament(tournament_name):
            print(f"[FILTERED] Турнир не разрешен: {tournament_name}")
            continue
    else:
        print("[OK] Турнир пропущен (None или N/A)")
    
    # Проверка статуса
    status_code = (details.get("status") or {}).get("code")
    if status_code in {"100", "110"}:
        print(f"[FILTERED] Матч завершен/приостановлен: {status_code}")
        continue
    print(f"[OK] Статус: {status_code}")
    
    # Проверка сетов
    result_score = _parse_pair(details.get("result_score"))
    sets_home = result_score[0] if result_score else 0
    sets_away = result_score[1] if result_score else 0
    set_diff = sets_home - sets_away
    
    result_scores = details.get("result_scores") or []
    current_set_index, current_games = _current_set_info(result_scores)
    games_home, games_away = current_games
    game_diff = games_home - games_away
    
    print(f"Сеты: {sets_home}:{sets_away} (разница: {set_diff})")
    print(f"Текущий сет: {current_set_index}, геймы: {games_home}:{games_away} (разница: {game_diff})")
    
    # Определение лидера
    leader_index = None
    if set_diff > 0:
        leader_index = 0
    elif set_diff < 0:
        leader_index = 1
    else:
        if abs(game_diff) < 2:
            print(f"[FILTERED] Нет лидера (сеты равны, разница геймов < 2)")
            continue
        leader_index = 0 if game_diff > 0 else 1
    
    trailing_index = 1 - leader_index
    print(f"[OK] Лидер: {leader_index}")
    
    # Проверка статистики
    stats_map = _extract_stats(details.get("statistic"))
    points = stats_map.get("points_won")
    breakpoints_won = stats_map.get("breakpoints_won")
    
    has_points = points and not math.isnan(points[0]) and not math.isnan(points[1])
    print(f"Points won: {points if has_points else 'НЕТ'}")
    
    if has_points:
        points_diff = points[leader_index] - points[trailing_index]
        print(f"Разница очков: {points_diff}")
        if points_diff < 4:
            print(f"[FILTERED] Разница очков < 4: {points_diff}")
            continue
    else:
        print("[INFO] Нет points_won, проверяем по сетам/геймам")
        if abs(set_diff) == 0:
            if abs(game_diff) < 3:
                print(f"[FILTERED] Сеты равны, разница геймов < 3: {abs(game_diff)}")
                continue
        elif abs(set_diff) == 1:
            if abs(game_diff) < 2:
                print(f"[FILTERED] Выигран 1 сет, разница геймов < 2: {abs(game_diff)}")
                continue
    
    has_breaks = breakpoints_won and not math.isnan(breakpoints_won[0]) and not math.isnan(breakpoints_won[1])
    if has_breaks:
        breaks_diff = breakpoints_won[leader_index] - breakpoints_won[trailing_index]
        print(f"Разница breaks: {breaks_diff}")
        if has_points and breaks_diff < 0:
            print(f"[FILTERED] Breaks_diff < 0 при наличии points: {breaks_diff}")
            continue
        elif not has_points and breaks_diff < -1:
            print(f"[FILTERED] Breaks_diff < -1 без points: {breaks_diff}")
            continue
    
    # Проверка раннего матча
    total_games_played = sum(sum(_parse_pair(entry.get("value")) or (0, 0)) for entry in result_scores)
    if total_games_played < 6 and max(sets_home, sets_away) == 0:
        if abs(game_diff) < 3:
            print(f"[FILTERED] Слишком рано: игр {total_games_played}, разница {abs(game_diff)}")
            continue
    
    # Проверка команд
    teams = details.get("teams") or []
    if len(teams) < 2:
        print(f"[FILTERED] Недостаточно команд: {len(teams)}")
        continue
    player_home = teams[0].get("name")
    player_away = teams[1].get("name")
    if not player_home or not player_away:
        print(f"[FILTERED] Нет имен игроков: home={player_home}, away={player_away}")
        continue
    
    print(f"[OK] Все проверки пройдены! {player_home} vs {player_away}")

