# -*- coding: utf-8 -*-
"""
Быстрая проверка статистики для тестового запроса 23:29 МСК
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("🔍 ПРОВЕРКА СТАТИСТИКИ - ТЕСТ 23:29 МСК")
print("=" * 60)

# Список матчей для проверки
matches = [
    {
        "sport": "⚽ ФУТБОЛ",
        "league": "Парагвай. Примера B",
        "team1": "Бенхамин Асеваль",
        "team2": "3 де Новембре",
        "score": "2:0 (64 мин)",
        "odds": "П1 1.02"
    },
    {
        "sport": "⚽ ФУТБОЛ",
        "league": "Кубок Либертадорес. Жен",
        "team1": "Депортиво Кали (ж)",
        "team2": "Насьональ Монтевидео (ж)",
        "score": "1:0 (70 мин)",
        "odds": "П1 1.10"
    },
    {
        "sport": "🎾 ТЕННИС",
        "league": "ATP Challenger. Фэрфилд. Хард. США",
        "team1": "Кинг Д.",
        "team2": "Грумет Г.",
        "score": "1:0 в сетах, 0:0 во 2-м",
        "odds": "П1 1.08"
    },
    {
        "sport": "🎾 ТЕННИС",
        "league": "UTR Pro Tennis Series. Жен. США",
        "team1": "Иванова Е.",
        "team2": "Нова А.",
        "score": "1:0 в сетах, 3:3 во 2-м",
        "odds": "П1 1.14"
    }
]

print("\n📋 МАТЧИ ДЛЯ ПРОВЕРКИ:\n")

for idx, match in enumerate(matches, 1):
    print(f"{idx}. {match['sport']}")
    print(f"   {match['league']}")
    print(f"   {match['team1']} - {match['team2']}")
    print(f"   Счет: {match['score']}")
    print(f"   Коэффициент: {match['odds']}")
    print()

print("=" * 60)
print("🌐 ИСТОЧНИКИ ПРОВЕРКИ:")
print("   • Flashscore.ru")
print("   • Scores24.live (резерв)")
print("   • Sofascore (резерв)")
print("=" * 60)
print("\n⏳ Начинаю проверку через Selenium...")

