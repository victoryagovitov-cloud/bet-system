#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_live_analyzer import LOWER_DIVISION_KEYWORDS, _normalize

test_name = "Чемпионат Европы до 19 лет, квалификация"
normalized = _normalize(test_name)
print(f"Исходное: {test_name}")
print(f"Нормализованное: {normalized}")

print("\nПроверка ключевых слов:")
for kw in LOWER_DIVISION_KEYWORDS:
    if kw in normalized:
        print(f"  НАЙДЕНО: '{kw}' в '{normalized}'")

