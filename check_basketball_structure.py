#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
import json

print("=" * 70)
print("ПРОВЕРКА СТРУКТУРЫ ДАННЫХ БАСКЕТБОЛА")
print("=" * 70)

raw_matches = fetch_live_matches(limit=5, sport="basketball")
print(f"\nНайдено матчей: {len(raw_matches)}")

if raw_matches:
    match = raw_matches[0]
    slug = match.get("slug")
    print(f"\nПервый матч: {slug}")
    print(f"\nСтруктура match_info:")
    print(json.dumps(match, indent=2, ensure_ascii=False)[:1000])
    
    try:
        details = fetch_match_stats(slug, sport="basketball")
        print(f"\nСтруктура details (первые 2000 символов):")
        details_str = json.dumps(details, indent=2, ensure_ascii=False)
        print(details_str[:2000])
        
        # Проверяем все поля, связанные с временем
        print(f"\nПоля, связанные с временем:")
        time_fields = ["minute", "period", "quarter", "time", "game_time", "elapsed_time"]
        for field in time_fields:
            value = details.get(field) or match.get(field)
            if value is not None:
                print(f"  {field}: {value} (type: {type(value).__name__})")
        
        # Проверяем game_state
        game_state = details.get("game_state", {})
        if game_state:
            print(f"\ngame_state:")
            print(json.dumps(game_state, indent=2, ensure_ascii=False)[:500])
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

