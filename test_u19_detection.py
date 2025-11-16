#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_live_analyzer import _normalize, LOWER_DIVISION_KEYWORDS, _is_tournament_allowed

test_tournaments = [
    "Катар. Чемпионат U19",
    "Чемпионат Европы до 19 лет, квалификация",
    "Молодежная лига до 19",
    "U19 Championship",
    "Championship U19",
]

print("Проверка распознавания U19 в турнирах:")
print("=" * 60)

for tournament in test_tournaments:
    normalized = _normalize(tournament)
    allowed = _is_tournament_allowed(tournament)
    
    print(f"\nТурнир: {tournament}")
    print(f"  Нормализовано: {normalized}")
    print(f"  Разрешен: {allowed}")
    
    # Проверяем, какие ключевые слова найдены
    found_keywords = [kw for kw in LOWER_DIVISION_KEYWORDS if kw in normalized]
    if found_keywords:
        print(f"  Найденные ключевые слова: {found_keywords}")
    else:
        print(f"  [ПРОБЛЕМА] Ключевые слова не найдены!")
        # Проверяем вручную
        if "u19" in normalized:
            print(f"    Но 'u19' ЕСТЬ в нормализованной строке!")
        if "u20" in normalized:
            print(f"    Но 'u20' ЕСТЬ в нормализованной строке!")
        if "u21" in normalized:
            print(f"    Но 'u21' ЕСТЬ в нормализованной строке!")

