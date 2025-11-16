#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Отладка парсинга счета в гандболе"""

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_handball_analyzer import _parse_int, _parse_score, _parse_minute
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 60)
print("ОТЛАДКА ПАРСИНГА СЧЕТА В ГАНДБОЛЕ")
print("=" * 60)

all_handball = fetch_live_matches(limit=20, sport="handball")
print(f"\n📊 Проверяю первые 10 матчей:\n")

for i, match_info in enumerate(all_handball[:10], 1):
    slug = match_info["slug"]
    teams = match_info.get("teams", [])
    home = teams[0].get("name", "?") if teams else "?"
    away = teams[1].get("name", "?") if len(teams) > 1 else "?"
    
    print(f"{i}. {home} vs {away}")
    
    try:
        details = fetch_match_stats(slug, sport="handball")
    except Exception as e:
        print(f"   ❌ Ошибка получения статистики: {e}\n")
        continue
    
    # Проверяем все возможные источники счета
    print("   📊 ИСТОЧНИКИ СЧЕТА:")
    
    game_state = details.get("game_state") or {}
    home_score_gs = game_state.get("home_score")
    away_score_gs = game_state.get("away_score")
    print(f"      game_state.home_score: {home_score_gs} (тип: {type(home_score_gs)})")
    print(f"      game_state.away_score: {away_score_gs} (тип: {type(away_score_gs)})")
    
    result_score = details.get("result_score")
    print(f"      result_score: {result_score} (тип: {type(result_score)})")
    
    game_score = details.get("game_score")
    print(f"      game_score: {game_score} (тип: {type(game_score)})")
    
    # Пробуем парсить
    home_score_parsed = _parse_int(home_score_gs)
    away_score_parsed = _parse_int(away_score_gs)
    print(f"      _parse_int(home_score): {home_score_parsed}")
    print(f"      _parse_int(away_score): {away_score_parsed}")
    
    if home_score_parsed is None or away_score_parsed is None:
        parsed_score = _parse_score(result_score)
        print(f"      _parse_score(result_score): {parsed_score}")
        if parsed_score:
            print(f"   ✅ Счет найден через result_score: {parsed_score[0]}:{parsed_score[1]}")
        else:
            # Пробуем game_score
            parsed_score = _parse_score(game_score)
            print(f"      _parse_score(game_score): {parsed_score}")
            if parsed_score:
                print(f"   ✅ Счет найден через game_score: {parsed_score[0]}:{parsed_score[1]}")
            else:
                print(f"   ❌ Счет не найден ни в одном источнике")
    else:
        print(f"   ✅ Счет найден через game_state: {home_score_parsed}:{away_score_parsed}")
    
    minute = details.get("minute") or match_info.get("minute")
    minute_parsed = _parse_minute(minute)
    print(f"   ⏰ Минута: {minute} → {minute_parsed}")
    
    print()

