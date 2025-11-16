# -*- coding: utf-8 -*-
"""
Быстрая проверка доступных матчей 23:35+ МСК
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("🔍 БЫСТРАЯ ПРОВЕРКА ДОСТУПНЫХ МАТЧЕЙ")
print("=" * 60)

matches = [
    {
        "id": 1,
        "sport": "⚽ ФУТБОЛ",
        "league": "Кубок Либертадорес (Женщины)",
        "team1": "Депортиво Кали (Ж)",
        "team2": "Насьональ Монтевидео (Ж)",
        "score": "1:0",
        "time": "76'",
        "odds_p1": 1.10,
        "available": True,
        "check_status": "✅ ДОСТУПЕН - анализируем!"
    },
    {
        "id": 2,
        "sport": "⚽ ФУТБОЛ",
        "league": "Парагвай PAR D3",
        "team1": "ФК Бенджамин Акеваль",
        "team2": "8 de Setiembre",
        "score": "2:1",
        "time": "71'",
        "odds_p1": 1.02,  # Очень низкий с BetBoom
        "available": True,
        "check_status": "⚠️ Коэф 1.02 - слишком низкий"
    }
]

print("\n📋 МАТЧИ ДЛЯ АНАЛИЗА:\n")

suitable = []

for match in matches:
    print(f"{match['id']}. {match['sport']}")
    print(f"   {match['league']}")
    print(f"   {match['team1']} - {match['team2']}")
    print(f"   Счет: {match['score']} ({match['time']})")
    print(f"   Коэффициент П1: {match['odds_p1']}")
    print(f"   Статус: {match['check_status']}")
    print()
    
    # Проверяем критерии
    if match['available'] and match['odds_p1'] >= 1.05:
        suitable.append(match)
        print(f"   ✅ ПОДХОДИТ для анализа!")
    else:
        print(f"   ❌ НЕ ПОДХОДИТ (коэф < 1.05)")
    print()

print("=" * 60)
print(f"📊 ИТОГО: {len(suitable)} матч(а) для детальной проверки")
print("=" * 60)

if suitable:
    print("\n🎯 ТРЕБУЕТСЯ ПРОВЕРКА СТАТИСТИКИ:")
    for match in suitable:
        print(f"   • {match['team1']} - {match['team2']}")
        print(f"     Проверить на Scores24/Flashscore/Sofascore")

