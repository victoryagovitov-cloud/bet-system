#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("=" * 70)
print("ВИДЫ СПОРТА В СИСТЕМЕ")
print("=" * 70)

sports = [
    {
        "name": "Футбол",
        "code": "soccer/football",
        "analyzer": "graphql_live_analyzer.py",
        "function": "analyze_live_matches",
        "status": "Активен",
        "features": [
            "Анализ по xG, владению, ударам",
            "Фильтрация молодежных/дружеских матчей",
            "Динамические требования по времени матча",
            "Ослабленные требования к статистике (possession ИЛИ shots_on_target)"
        ]
    },
    {
        "name": "Теннис",
        "code": "tennis",
        "analyzer": "graphql_tennis_analyzer.py",
        "function": "analyze_live_tennis_matches",
        "status": "Активен",
        "features": [
            "Анализ по сетам и геймам",
            "Поддержка ITF турниров (если есть статистика)",
            "Учет очков, брейков, подач",
            "Анализ по сетам, а не по минутам"
        ]
    },
    {
        "name": "Баскетбол",
        "code": "basketball",
        "analyzer": "graphql_basketball_analyzer.py",
        "function": "analyze_live_basketball_matches",
        "status": "Активен (НОВЫЙ)",
        "features": [
            "Анализ по очкам, подборам, передачам",
            "Использует счет как основную метрику",
            "Учет времени через четверти (40 минут)",
            "Динамические требования по времени матча"
        ]
    },
    {
        "name": "Гандбол",
        "code": "handball",
        "analyzer": "graphql_handball_analyzer.py",
        "function": "analyze_live_handball_matches",
        "status": "Активен (включен обратно)",
        "features": [
            "Анализ по счету и темпу игры",
            "Исправлена ошибка: счет НЕ равен минутам",
            "Требует минимум 32 минуты матча",
            "Прогноз общего счета (ТБ/ТМ)"
        ]
    }
]

for i, sport in enumerate(sports, 1):
    print(f"\n{i}. {sport['name'].upper()} ({sport['code']})")
    print(f"   Статус: {sport['status']}")
    print(f"   Анализатор: {sport['analyzer']}")
    print(f"   Функция: {sport['function']}")
    print(f"   Особенности:")
    for feature in sport['features']:
        print(f"     - {feature}")

print("\n" + "=" * 70)
print("ИТОГО: 4 вида спорта")
print("=" * 70)
print("\nПриоритет отбора:")
print("  1. Футбол (основной)")
print("  2. Теннис (если нет футбола или есть свободные слоты)")
print("  3. Баскетбол (если есть свободные слоты)")
print("  4. Гандбол (если есть свободные слоты)")

print("\n" + "=" * 70)
print("НАСТРОЙКИ ОБЩИЕ ДЛЯ ВСЕХ ВИДОВ СПОРТА")
print("=" * 70)
print("  - MIN_ODDS = 1.01")
print("  - PRIMARY_MAX_ODDS = 1.10 (безопасные матчи)")
print("  - EXTENDED_MAX_ODDS = 1.50 (интересные матчи)")
print("  - EXTENDED_MIN_DOMINANCE = 6.0")
print("  - Приоритизация: сначала по коэффициентам, потом по dominance")
print("  - Дедупликация: 4 часа")
print("  - Максимум матчей в сообщении: 5")

