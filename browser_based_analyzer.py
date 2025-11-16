#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
АНАЛИЗ МАТЧЕЙ ЧЕРЕЗ BROWSER MCP

Использует браузер для парсинга BetBoom в реальном времени
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime

# Структура для хранения матчей
class LiveMatch:
    def __init__(self, team1, team2, score, league, time, coef_p1, coef_p2):
        self.team1 = team1
        self.team2 = team2
        self.score = score
        self.league = league
        self.time = time
        self.coef_p1 = coef_p1
        self.coef_p2 = coef_p2
    
    def __repr__(self):
        return f"{self.team1} {self.score} {self.team2} ({self.league})"


def analyze_from_browser_data(matches_data):
    """
    Анализирует матчи полученные через Browser MCP
    
    matches_data должен быть список матчей с полями:
    {
        'team1': 'АЗ Алкмаар',
        'team2': 'ПСВ Эйндховен',
        'score': '0-3',
        'league': 'Нидерланды. Эредивизи',
        'time': '1Т, 29 мин',
        'coef_p1': 60.0,
        'coef_p2': 1.03
    }
    """
    
    print("=" * 90)
    print("АНАЛИЗ LIVE-МАТЧЕЙ (через Browser MCP)")
    print("=" * 90)
    print()
    
    recommendations = []
    
    for match_data in matches_data:
        # Парсим счет
        score_parts = match_data['score'].split('-')
        score1 = int(score_parts[0])
        score2 = int(score_parts[1])
        
        # ШАГИ АНАЛИЗА
        # 1. Определяем фаворита по коэффициентам
        coef_p1 = match_data['coef_p1']
        coef_p2 = match_data['coef_p2']
        
        if coef_p1 < coef_p2:
            favorite = match_data['team1']
            favorite_coef = coef_p1
            is_p1_favorite = True
        else:
            favorite = match_data['team2']
            favorite_coef = coef_p2
            is_p1_favorite = False
        
        # 2. Определяем лидера
        if score1 > score2:
            leader = match_data['team1']
            leader_score = f"{score1}:{score2}"
            is_p1_leader = True
        elif score2 > score1:
            leader = match_data['team2']
            leader_score = f"{score2}:{score1}"
            is_p1_leader = False
        else:
            leader = None
            leader_score = None
            is_p1_leader = None
        
        # 3. Проверяем: ведет ли фаворит?
        favorite_leads = (is_p1_favorite == is_p1_leader)
        
        # 4. Формируем результат
        result = {
            'team1': match_data['team1'],
            'team2': match_data['team2'],
            'score': match_data['score'],
            'league': match_data['league'],
            'time': match_data['time'],
            'favorite': favorite,
            'favorite_coef': favorite_coef,
            'leader': leader,
            'leader_score': leader_score,
            'favorite_leads': favorite_leads,
            'recommendation': 'ПРИНЯТЬ' if favorite_leads else 'ОТКЛОНИТЬ'
        }
        
        # 5. Добавляем в рекомендации если подходит
        if favorite_leads:
            recommendations.append(result)
        
        # 6. Выводим результат
        status = "✓ РЕКОМЕНДУЕМ" if favorite_leads else "✗ ОТКЛОНЯЕМ"
        
        print(f"⚽ {result['team1']} vs {result['team2']}")
        print(f"   Счет: {result['score']} ({result['time']})")
        print(f"   Лига: {result['league']}")
        print(f"   Фаворит: {result['favorite']} (кэф ~{result['favorite_coef']:.2f})")
        print(f"   Лидирует: {result['leader']} {result['leader_score']}" if result['leader'] else "   Ничья")
        print(f"   → {status}")
        print()
    
    # ИТОГИ
    print("=" * 90)
    print(f"ВСЕГО МАТЧЕЙ: {len(matches_data)}")
    print(f"РЕКОМЕНДУЕМЫХ: {len(recommendations)}")
    print("=" * 90)
    print()
    
    if recommendations:
        print("📋 ФИНАЛЬНЫЕ РЕКОМЕНДАЦИИ:")
        print()
        for rec in recommendations:
            print(f"  1️⃣ {rec['team1']} vs {rec['team2']}")
            print(f"     Счет: {rec['score']} ({rec['time']})")
            print(f"     Лига: {rec['league']}")
            print(f"     СТАВКА НА: {rec['favorite']} при кэфе ~{rec['favorite_coef']:.2f}")
            print()
    
    print("=" * 90)
    print(f"Время анализа: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 90)
    print()
    
    return recommendations


# ============================================================================
# ИНСТРУКЦИИ ДЛЯ ИСПОЛЬЗОВАНИЯ
# ============================================================================

def print_usage():
    """Выводит инструкции по использованию"""
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  КАК ИСПОЛЬЗОВАТЬ ЭТОТ АНАЛИЗАТОР                         ║
╚════════════════════════════════════════════════════════════════════════════╝

1. ОТКРОЙТЕ BetBoom В БРАУЗЕРЕ:
   https://betboom.ru/sport/football?period=all&type=live

2. ПОДКЛЮЧИТЕ Browser MCP (если еще не подключен):
   - Нажмите на иконку Browser MCP расширения
   - Нажмите "Connect"

3. ВОЗЬМИТЕ ДАННЫЕ МАТЧЕЙ:
   - Откройте консоль Python
   - Импортируйте этот файл
   - Вызовите функцию с данными матчей:

   from browser_based_analyzer import analyze_from_browser_data
   
   matches = [
       {
           'team1': 'АЗ Алкмаар',
           'team2': 'ПСВ Эйндховен',
           'score': '0-3',
           'league': 'Нидерланды. Эредивизи',
           'time': '1Т, 29 мин',
           'coef_p1': 60.0,
           'coef_p2': 1.03
       },
       # ... другие матчи
   ]
   
   recommendations = analyze_from_browser_data(matches)

4. ОТПРАВЬТЕ РЕКОМЕНДАЦИИ В TELEGRAM:
   - Скопируйте результаты из recommendations
   - Отправьте в канал @TrueLiveBet по шаблону

═════════════════════════════════════════════════════════════════════════════
""")


# ============================================================================
# ТЕСТИРОВАНИЕ
# ============================================================================

if __name__ == '__main__':
    print_usage()
    
    # Тестовые данные
    test_matches = [
        {
            'team1': 'АЗ Алкмаар',
            'team2': 'ПСВ Эйндховен',
            'score': '0-3',
            'league': 'Нидерланды. Эредивизи',
            'time': '1Т, 29 мин',
            'coef_p1': 60.0,
            'coef_p2': 1.03
        },
        {
            'team1': 'Боде Глимт',
            'team2': 'Брюн',
            'score': '1-0',
            'league': 'Норвегия. Элитсерия',
            'time': '1Т, 16 мин',
            'coef_p1': 1.03,
            'coef_p2': 45.0
        },
        {
            'team1': 'Сент Трюйден',
            'team2': 'Стандард Льеж',
            'score': '1-0',
            'league': 'Бельгия. 1-й дивизион',
            'time': '2Т, 57 мин',
            'coef_p1': 1.18,
            'coef_p2': 20.0
        }
    ]
    
    print("\n" + "=" * 90)
    print("ТЕСТИРОВАНИЕ АНАЛИЗАТОРА")
    print("=" * 90)
    print()
    
    recommendations = analyze_from_browser_data(test_matches)

