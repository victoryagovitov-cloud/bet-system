#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_live_analyzer import _normalize, LOWER_DIVISION_KEYWORDS

test = "Молодежная лига до 19"
normalized = _normalize(test)

print(f"Исходный турнир: {test}")
print(f"Нормализованный: {repr(normalized)}")
print(f"\nПроверка ключевых слов:")

for kw in LOWER_DIVISION_KEYWORDS:
    if kw in normalized:
        print(f"  [НАЙДЕНО] '{kw}' в '{normalized}'")
    # Также проверяем обратное - может быть проблема с пробелами
    elif normalized in kw:
        print(f"  [ОБРАТНОЕ] '{normalized}' содержится в '{kw}'")

# Проверяем конкретно нужные ключевые слова
important_keywords = ["до 19", "молодеж", "молодёж"]
print(f"\nПроверка важных ключевых слов:")
for kw in important_keywords:
    found = kw in normalized
    print(f"  '{kw}' в '{normalized}': {found}")
    if found:
        idx = normalized.find(kw)
        print(f"    Позиция: {idx}, контекст: ...{normalized[max(0,idx-5):idx+len(kw)+5]}...")

