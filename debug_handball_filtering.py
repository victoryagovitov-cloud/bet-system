#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_handball_analyzer import _parse_minute, _parse_score, _is_allowed_handball_tournament

print("=" * 60)
print("ДЕТАЛЬНАЯ ПРОВЕРКА ФИЛЬТРАЦИИ ГАНДБОЛА")
print("=" * 60)

raw_matches = fetch_live_matches(limit=10, sport="handball")
print(f"\nНайдено raw матчей: {len(raw_matches)}")

MINIMUM_MINUTE_THRESHOLD = 32

for i, match in enumerate(raw_matches[:5], 1):
    slug = match.get("slug", "?")
    teams = match.get("teams", [])
    home = teams[0].get("name", "?") if teams else "?"
    away = teams[1].get("name", "?") if len(teams) > 1 else "?"
    tournament = match.get("tournament_name")
    
    print(f"\n{i}. {home} vs {away}")
    print(f"   Slug: {slug}")
    print(f"   Tournament: {tournament}")
    
    # Получаем статистику
    try:
        details = fetch_match_stats(slug, sport="handball")
        
        # Проверяем турнир
        tournament_name = details.get("tournament_name") or tournament
        is_allowed = _is_allowed_handball_tournament(tournament_name)
        print(f"   Tournament allowed: {is_allowed}")
        if not is_allowed:
            print(f"   [FILTERED] Турнир не разрешен")
            continue
        
        # Проверяем минуты
        minute = details.get("minute")
        minute_numeric = _parse_minute(minute)
        print(f"   Minute: {minute} -> {minute_numeric}")
        
        if minute_numeric is None:
            print(f"   [FILTERED] Нет минут")
            continue
        
        if minute_numeric < MINIMUM_MINUTE_THRESHOLD:
            print(f"   [FILTERED] Минута {minute_numeric} < {MINIMUM_MINUTE_THRESHOLD}")
            continue
        
        # Проверяем счет
        game_score = details.get("game_score")
        result_score = details.get("result_score")
        score = _parse_score(game_score) or _parse_score(result_score)
        print(f"   Score: {game_score} / {result_score} -> {score}")
        
        if not score:
            print(f"   [FILTERED] Нет счета")
            continue
        
        home_score, away_score = score
        total_score = home_score + away_score
        score_diff = abs(home_score - away_score)
        
        print(f"   Total score: {total_score}, diff: {score_diff}")
        
        if total_score < 20:
            print(f"   [FILTERED] total_score {total_score} < 20")
            continue
        
        # Проверяем разницу в счете
        diff_threshold = 3 if minute_numeric >= 50 else (4 if minute_numeric >= 40 else 5)
        if score_diff < diff_threshold:
            print(f"   [FILTERED] score_diff {score_diff} < {diff_threshold}")
            continue
        
        print(f"   [OK] ПРОШЕЛ ВСЕ ФИЛЬТРЫ")
        
    except Exception as e:
        print(f"   [ERROR] Ошибка при получении статистики: {e}")

print("\n" + "=" * 60)

