#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
import json

print("=" * 70)
print("ПРОВЕРКА ФОРМАТА СЧЕТА В БАСКЕТБОЛЕ")
print("=" * 70)

all_matches = fetch_live_matches(limit=10, sport="basketball")
print(f"\nВсего матчей: {len(all_matches)}")

if len(all_matches) == 0:
    print("Нет матчей")
    exit(0)

# Проверяем первый матч детально
match_info = all_matches[0]
slug = match_info.get("slug", "")

print(f"\nМатч: {slug}")

try:
    details = fetch_match_stats(slug, sport="basketball")
    
    print("\nДоступные поля для счета:")
    print(f"  game_score: {details.get('game_score')}")
    print(f"  game_state: {details.get('game_state')}")
    
    game_state = details.get("game_state") or {}
    print(f"  game_state.home_score: {game_state.get('home_score')}")
    print(f"  game_state.away_score: {game_state.get('away_score')}")
    
    # Показываем структуру полностью
    print("\nПолная структура game_state:")
    print(json.dumps(game_state, indent=2, ensure_ascii=False, default=str))
    
    # Проверяем альтернативные источники
    print("\nАльтернативные источники счета:")
    print(f"  result_score: {details.get('result_score')}")
    print(f"  score: {details.get('score')}")
    
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()

