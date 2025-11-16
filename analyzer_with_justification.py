#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
АНАЛИЗ LIVE-МАТЧЕЙ С ОБОСНОВАНИЕМ

Версия с красивым форматированием и объяснением каждой рекомендации
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime

def format_justification(result):
    """Формирует обоснование для матча"""
    
    favorite = result['favorite']
    score = result['score']
    coef = result['favorite_coef']
    leader = result['leader']
    
    if result['recommendation'] == 'ПРИНЯТЬ':
        # Определяем насколько уверены
        if coef < 1.2:
            confidence = "очень уверен"
            emoji = "🔥"
        elif coef < 1.5:
            confidence = "уверен"
            emoji = "✓"
        else:
            confidence = "доминирует"
            emoji = "💪"
        
        justification = f"""📊 ОБОСНОВАНИЕ:
  • {favorite} - фаворит ({emoji} букмекер {confidence}, кэф {coef:.2f})
  • На поле контролирует (счет {score})
  • Рекомендуем ставку"""
    else:
        justification = f"""⚠️ НЕ РЕКОМЕНДУЕМ:
  • Фаворит не подтвердил статус
  • На поле ведет аутсайдер
  • Высокий риск"""
    
    return justification


def analyze_from_browser_data(matches_data):
    """
    Анализирует матчи полученные через Browser MCP
    С красивым форматированием и обоснованием
    """
    
    print()
    print("╔" + "=" * 88 + "╗")
    print("║" + " " * 20 + "LIVE-АНАЛИЗ МАТЧЕЙ" + " " * 50 + "║")
    print("║" + " " * 25 + datetime.now().strftime("%H:%M МСК") + " " * 54 + "║")
    print("╚" + "=" * 88 + "╝")
    print()
    
    recommendations = []
    rejected = []
    
    for idx, match_data in enumerate(matches_data, 1):
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
        else:
            rejected.append(result)
        
        # 6. Выводим результат с красивым форматированием
        print(f"{'─' * 90}")
        print(f"⚽ {result['team1']} vs {result['team2']}")
        print(f"   Счет: {result['score']} ({result['time']}) | {result['league']}")
        print(f"   Фаворит: {result['favorite']} (кэф ~{result['favorite_coef']:.2f})")
        
        # Добавляем обоснование
        justification = format_justification(result)
        print(justification)
        
        if result['recommendation'] == 'ПРИНЯТЬ':
            print(f"   💰 КЭФ: ~{result['favorite_coef']:.2f}")
            print(f"   ✅ СТАВИМ НА: {result['favorite']}")
        
        print()
    
    # ИТОГИ
    print("╔" + "=" * 88 + "╗")
    print(f"║ ИТОГО: {len(recommendations)} РЕКОМЕНДАЦИЙ ИЗ {len(matches_data)} МАТЧЕЙ" + " " * (88 - len(f" ИТОГО: {len(recommendations)} РЕКОМЕНДАЦИЙ ИЗ {len(matches_data)} МАТЧЕЙ") - 1) + "║")
    print("╚" + "=" * 88 + "╝")
    print()
    
    if recommendations:
        print("📋 ФИНАЛЬНЫЕ РЕКОМЕНДАЦИИ:")
        print()
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}️⃣ {rec['team1']} vs {rec['team2']}")
            print(f"     Счет: {rec['score']} | Лига: {rec['league']}")
            print(f"     ➜ СТАВИМ НА: {rec['favorite']}")
            print(f"     💰 Кэф BetBoom: ~{rec['favorite_coef']:.2f}")
            print()
    else:
        print("❌ НЕ НАЙДЕНО ПОДХОДЯЩИХ МАТЧЕЙ")
        print()
    
    print("╔" + "=" * 88 + "╗")
    print(f"║ Анализ завершен: {datetime.now().strftime('%H:%M:%S МСК')}" + " " * (88 - len(f" Анализ завершен: {datetime.now().strftime('%H:%M:%S МСК')}") - 1) + "║")
    print("╚" + "=" * 88 + "╝")
    print()
    
    return recommendations


# ============================================================================
# ТЕСТИРОВАНИЕ
# ============================================================================

if __name__ == '__main__':
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
        },
        {
            'team1': 'Фрайбург',
            'team2': 'Санкт-Паули',
            'score': '2-1',
            'league': 'Германия. Бундеслига',
            'time': '2Т, 89 мин',
            'coef_p1': 1.50,
            'coef_p2': 4.5
        },
        {
            'team1': 'Ахмат Грозный',
            'team2': 'Спартак Москва',
            'score': '1-2',
            'league': 'Россия. Премьер-лига',
            'time': '2Т, 88 мин',
            'coef_p1': 3.5,
            'coef_p2': 2.2
        }
    ]
    
    print("\n" + "=" * 90)
    print("ТЕСТИРОВАНИЕ АНАЛИЗАТОРА С ОБОСНОВАНИЕМ")
    print("=" * 90)
    
    recommendations = analyze_from_browser_data(test_matches)

