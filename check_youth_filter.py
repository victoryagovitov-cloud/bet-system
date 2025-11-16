#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_live_analyzer import _is_tournament_allowed, _is_youth_team, _normalize

print("Проверка фильтрации молодежки:")
print("=" * 60)

# Тестовые данные из скриншотов
test_cases = [
    {
        "tournament": "Катар. Чемпионат U19",
        "home": "Аль Райан U19",
        "away": "Катар СК Доха U19"
    },
    {
        "tournament": "Чемпионат Европы до 19 лет, квалификация",
        "home": "Португалия U19",
        "away": "Эстония U19"
    },
    {
        "tournament": "Молодежная лига до 19",
        "home": "Эр-Райян до 19",
        "away": "Катар Доха до 19"
    }
]

for i, case in enumerate(test_cases, 1):
    print(f"\n{i}. Матч:")
    print(f"   Турнир: {case['tournament']}")
    print(f"   Команды: {case['home']} vs {case['away']}")
    
    tournament_allowed = _is_tournament_allowed(case['tournament'])
    home_youth = _is_youth_team(case['home'])
    away_youth = _is_youth_team(case['away'])
    
    print(f"\n   Проверка турнира: {'РАЗРЕШЕН' if tournament_allowed else 'ЗАПРЕЩЕН'}")
    print(f"   Команда1 молодежка: {home_youth}")
    print(f"   Команда2 молодежка: {away_youth}")
    
    if not tournament_allowed:
        print(f"   [OK] МАТЧ ОТФИЛЬТРОВАН по турниру")
    elif home_youth or away_youth:
        print(f"   [OK] МАТЧ ОТФИЛЬТРОВАН по названию команды")
    else:
        print(f"   [ERROR] МАТЧ ПРОШЕЛ ФИЛЬТР - ОШИБКА!")

print("\n" + "=" * 60)
print("\nПроверка нормализации:")
test_names = ["Аль Райан U19", "Эр-Райян до 19", "Португалия U19"]
for name in test_names:
    normalized = _normalize(name)
    print(f"  '{name}' -> '{normalized}'")

