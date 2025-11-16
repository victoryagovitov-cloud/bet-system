#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_live_analyzer import _is_tournament_allowed
from graphql_tennis_analyzer import _is_allowed_tennis_tournament

print("Проверка фильтра молодежки:")
tests = [
    "Чемпионат Европы до 19 лет, квалификация",
    "Молодежная лига до 19",
    "Премьер-лига",
    "Лига чемпионов",
]
for t in tests:
    result = _is_tournament_allowed(t)
    print(f"  {t}: {'РАЗРЕШЕН' if result else 'ЗАПРЕЩЕН'}")

print("\nПроверка фильтра тенниса:")
tennis_tests = [
    "N/A",
    None,
    "",
    "ATP Masters",
    "WTA Tour",
    "ITF Futures",
]
for t in tennis_tests:
    result = _is_allowed_tennis_tournament(t)
    print(f"  {repr(t)}: {'РАЗРЕШЕН' if result else 'ЗАПРЕЩЕН'}")

