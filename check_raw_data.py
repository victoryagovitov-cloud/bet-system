#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches

print("=" * 70)
print("ПРОВЕРКА СЫРЫХ ДАННЫХ С SCORES24")
print("=" * 70)

all_matches = fetch_live_matches()
print(f"\nВсего матчей: {len(all_matches)}")

if len(all_matches) == 0:
    print("Нет матчей")
    exit(0)

# Показываем первые 3 матча полностью
for i, match in enumerate(all_matches[:3], 1):
    print(f"\n{'='*70}")
    print(f"МАТЧ {i}:")
    print(f"{'='*70}")
    
    # Показываем все ключи
    print("\nДоступные поля:")
    for key in sorted(match.keys()):
        value = match[key]
        if isinstance(value, str) and len(value) > 50:
            value = value[:50] + "..."
        print(f"  {key}: {value}")
    
    # Особое внимание на sport
    sport = match.get("sport")
    print(f"\n[SPORT] = {repr(sport)}")
    
    # Проверяем альтернативные поля
    if "sport_type" in match:
        print(f"[SPORT_TYPE] = {repr(match.get('sport_type'))}")
    if "sportId" in match:
        print(f"[SPORT_ID] = {repr(match.get('sportId'))}")

print("\n" + "=" * 70)
print("ПОИСК ФУТБОЛА И ТЕННИСА ПО АЛЬТЕРНАТИВНЫМ ПОЛЯМ")
print("-" * 70)

# Пробуем найти по другим полям
soccer_found = 0
tennis_found = 0

for match in all_matches:
    # Проверяем разные варианты определения спорта
    sport = match.get("sport")
    sport_type = match.get("sport_type")
    sport_id = match.get("sportId")
    tournament = match.get("tournament_name", "").lower()
    
    # Футбол
    if (sport == "soccer" or sport_type == "soccer" or 
        sport_id == 1 or "football" in tournament or 
        "футбол" in tournament):
        soccer_found += 1
    
    # Теннис
    if (sport == "tennis" or sport_type == "tennis" or 
        sport_id == 2 or "tennis" in tournament or 
        "теннис" in tournament):
        tennis_found += 1

print(f"Найдено футбола (по разным критериям): {soccer_found}")
print(f"Найдено тенниса (по разным критериям): {tennis_found}")

if soccer_found == 0 and tennis_found == 0:
    print("\n[ВЫВОД] Действительно нет футбола и тенниса")
    print("Это не проблема фильтров - просто нет матчей")

