#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка конкретных матчей из BetBoom на Scores24
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from fast_stats_collector import get_match_stats_fast

def main():
    print("🔍 ПРОВЕРКА КОНКРЕТНЫХ МАТЧЕЙ НА SCORES24")
    print("="*60)
    
    # ТОП-КАНДИДАТЫ ИЗ BETBOOM
    matches_to_check = [
        # ФУТБОЛ - ИНТЕРЕСНЫЕ МАТЧИ
        {"team1": "Антальяспор", "team2": "Бешикташ", "sport": "football", "score": "0:2", "time": "1Т, 34 мин"},
        {"team1": "Марсель", "team2": "Брест", "sport": "football", "score": "2:0", "time": "2Т, 76 мин"},
        {"team1": "Атлетико М", "team2": "Леванте", "sport": "football", "score": "0:0", "time": "1Т, 5 мин"},
        {"team1": "Ювентус", "team2": "Торино", "sport": "football", "score": "0:0", "time": "1Т, 35 мин"},
        
        # ТЕННИС - ИНТЕРЕСНЫЕ МАТЧИ  
        {"team1": "Урхобо А.", "team2": "Веддер Е.", "sport": "tennis", "score": "0:0 (2:5)", "time": "1-й сет"},
        {"team1": "Норри К.", "team2": "Тиен Л.", "sport": "tennis", "score": "1:1 (5:6)", "time": "3-й сет"},
        {"team1": "Грунчакова В.", "team2": "Йокич К.", "sport": "tennis", "score": "0:0 (1:1)", "time": "1-й сет"},
        
        # ГАНДБОЛ - ИНТЕРЕСНЫЕ МАТЧИ
        {"team1": "Дессау-Росслауэр", "team2": "ГК Оппенвейлер/Бекнанг", "sport": "handball", "score": "14:14", "time": "1Т, 28 мин"},
        {"team1": "Минден", "team2": "Мельзунген", "sport": "handball", "score": "12:12", "time": "1Т, 30 мин"},
        {"team1": "Кобург", "team2": "Хюттенберг", "sport": "handball", "score": "15:13", "time": "1Т, 28 мин"},
    ]
    
    results = []
    
    for i, match in enumerate(matches_to_check, 1):
        print(f"\n🔎 [{i}/{len(matches_to_check)}] {match['team1']} - {match['team2']}")
        print(f"   📊 {match['score']} ({match['time']})")
        
        # Проверяем статистику
        stats = get_match_stats_fast(match['team1'], match['team2'], match['sport'])
        
        if stats and stats.get('found'):
            print(f"   ✅ НАЙДЕНО на Scores24!")
            print(f"   📈 Статистика: {stats.get('summary', 'Нет данных')}")
            results.append({
                'match': match,
                'stats': stats,
                'status': 'found'
            })
        else:
            print(f"   ❌ НЕ НАЙДЕНО на Scores24")
            results.append({
                'match': match,
                'stats': None,
                'status': 'not_found'
            })
    
    # Сводка результатов
    print("\n" + "="*60)
    print("📋 СВОДКА РЕЗУЛЬТАТОВ:")
    print("="*60)
    
    found_count = len([r for r in results if r['status'] == 'found'])
    print(f"✅ Найдено на Scores24: {found_count}/{len(results)}")
    print(f"❌ Не найдено: {len(results) - found_count}/{len(results)}")
    
    # Детали найденных матчей
    for result in results:
        if result['status'] == 'found':
            match = result['match']
            stats = result['stats']
            print(f"\n🎯 {match['team1']} - {match['team2']} ({match['sport']})")
            print(f"   📊 {match['score']} | {match['time']}")
            print(f"   📈 {stats.get('summary', 'Нет данных')}")
    
    return results

if __name__ == "__main__":
    main()
