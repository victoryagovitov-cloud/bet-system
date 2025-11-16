#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_live_analyzer import _is_tournament_allowed

print("Проверка фильтрации товарищеских матчей:")
print("=" * 60)

test_tournaments = [
    "Товарищеские матчи, сборные",
    "Friendly Match",
    "Дружеский матч",
    "Test Match",
    "Подготовительный матч",
    "Премьер-лига",
    "Лига чемпионов",
    "Чемпионат мира",
    "Euro 2024",
]

for tournament in test_tournaments:
    allowed = _is_tournament_allowed(tournament)
    status = "[OK] ЗАПРЕЩЕН" if not allowed else "[ERROR] РАЗРЕШЕН"
    print(f"{tournament}: {status}")

