#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
УЛЬТРАБЫСТРЫЙ АНАЛИЗ МАТЧЕЙ
Время: 2-3 сек на 20 матчей
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

print("=" * 80)
print("УЛЬТРАБЫСТРЫЙ АНАЛИЗАТОР МАТЧЕЙ")
print("=" * 80)
print()

# ============================================================================
# СИМУЛЯЦИЯ ДАННЫХ BETBOOM (вместо парсинга, используем готовые данные)
# ============================================================================

SAMPLE_MATCHES = [
    {
        'id': 1,
        'team1': 'АЗ Алкмаар',
        'team2': 'ПСВ Эйндховен',
        'score': '0-3',
        'league': 'Нидерланды. Эредивизи',
        'time': '1Т, 29 мин',
        'coef_p1': 60.0,  # коэф П1
        'coef_x': 18.0,   # коэф Х
        'coef_p2': 1.03   # коэф П2
    },
    {
        'id': 2,
        'team1': 'Боде Глимт',
        'team2': 'Брюн',
        'score': '1-0',
        'league': 'Норвегия. Элитсерия',
        'time': '1Т, 16 мин',
        'coef_p1': 1.03,
        'coef_x': 13.0,
        'coef_p2': 45.0
    },
    {
        'id': 3,
        'team1': 'Сент Трюйден',
        'team2': 'Стандард Льеж',
        'score': '1-0',
        'league': 'Бельгия. 1-й дивизион',
        'time': '2Т, 57 мин',
        'coef_p1': 1.18,
        'coef_x': 5.9,
        'coef_p2': 20.0
    }
]

# ============================================================================
# ФУНКЦИЯ 1: Определить фаворита по коэффициентам (БЫСТРО)
# ============================================================================

def get_favorite_by_coef(match):
    """
    Определяем фаворита по коэффициентам
    Меньший коэф = выше вероятность = фаворит
    """
    coef_p1 = match['coef_p1']
    coef_p2 = match['coef_p2']
    
    if coef_p1 < coef_p2:
        return 'team1', coef_p1
    else:
        return 'team2', coef_p2

# ============================================================================
# ФУНКЦИЯ 2: Парсить счет
# ============================================================================

def parse_score(score_str):
    """Парсит счет '0-3' → (0, 3)"""
    parts = score_str.split('-')
    return int(parts[0]), int(parts[1])

# ============================================================================
# ФУНКЦИЯ 3: Проверить, ведет ли фаворит
# ============================================================================

def check_favorite_leads(match):
    """
    Основная логика:
    1. Определяем фаворита по коэффициентам
    2. Проверяем, ведет ли он в счете
    """
    favorite_key, coef = get_favorite_by_coef(match)
    
    # Парсим счет
    score1, score2 = parse_score(match['score'])
    
    # Кто ведет?
    if score1 > score2:
        leader = 'team1'
    elif score2 > score1:
        leader = 'team2'
    else:
        leader = None  # ничья (не должна быть, но на случай)
    
    # Фаворит ведет?
    if favorite_key == leader:
        leads = True
    else:
        leads = False
    
    return {
        'match_id': match['id'],
        'team1': match['team1'],
        'team2': match['team2'],
        'score': match['score'],
        'league': match['league'],
        'time': match['time'],
        'favorite': match['team1'] if favorite_key == 'team1' else match['team2'],
        'leader': match['team1'] if leader == 'team1' else (match['team2'] if leader == 'team2' else 'ничья'),
        'favorite_leads': leads,
        'recommendation': 'ПРИНЯТЬ' if leads else 'ОТКЛОНИТЬ',
        'coef_favorite': coef
    }

# ============================================================================
# ФУНКЦИЯ 4: Анализ одного матча (для параллельного выполнения)
# ============================================================================

def analyze_single_match(match):
    """
    Анализирует один матч
    Время: 0.1 сек (почти мгновенно)
    """
    time.sleep(0.05)  # имитация работы (обычно нет задержки)
    return check_favorite_leads(match)

# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ: Параллельный анализ всех матчей
# ============================================================================

def analyze_matches_fast(matches):
    """
    ПАРАЛЛЕЛЬНЫЙ анализ матчей
    
    Вместо:
      Матч 1 → 0.1 сек
      Матч 2 → 0.1 сек
      Матч 3 → 0.1 сек
      ИТОГО: 0.3 сек
    
    Делаем:
      Матч 1, 2, 3 одновременно → 0.1 сек!
      ИТОГО: 0.1 сек
    """
    print(f"Анализирую {len(matches)} матчей параллельно...")
    print()
    
    results = []
    
    # Используем ThreadPoolExecutor для параллельного выполнения
    # max_workers=5 означает 5 одновременных потоков
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Запускаем все задачи
        futures = {executor.submit(analyze_single_match, match): match for match in matches}
        
        # Собираем результаты по мере готовности
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
    
    return results

# ============================================================================
# ВЫВОД РЕЗУЛЬТАТОВ
# ============================================================================

def print_results(results):
    """Красиво выводит результаты"""
    
    print("=" * 80)
    print("РЕЗУЛЬТАТЫ АНАЛИЗА")
    print("=" * 80)
    print()
    
    recommendations = [r for r in results if r['recommendation'] == 'ПРИНЯТЬ']
    
    for i, result in enumerate(results, 1):
        status = "✓ РЕКОМЕНДУЕМ" if result['recommendation'] == 'ПРИНЯТЬ' else "✗ ОТКЛОНЯЕМ"
        
        print(f"Матч #{result['match_id']}: {result['team1']} vs {result['team2']}")
        print(f"  Лига: {result['league']}")
        print(f"  Счет: {result['score']} ({result['time']})")
        print(f"  Фаворит: {result['favorite']} (кэф ~{result['coef_favorite']:.2f})")
        print(f"  Лидирует: {result['leader']}")
        print(f"  → {status}")
        print()
    
    print("=" * 80)
    print(f"ИТОГО РЕКОМЕНДАЦИЙ: {len(recommendations)}")
    print("=" * 80)
    print()
    
    if recommendations:
        print("РЕКОМЕНДУЕМЫЕ МАТЧИ:")
        for rec in recommendations:
            print(f"  • {rec['team1']} vs {rec['team2']} - {rec['score']} ({rec['league']})")
            print(f"    Ставка на: {rec['favorite']} при кэфе ~{rec['coef_favorite']:.2f}")
        print()

# ============================================================================
# ЗАПУСК
# ============================================================================

if __name__ == '__main__':
    print()
    print(f"Количество матчей для анализа: {len(SAMPLE_MATCHES)}")
    print()
    
    # Засекаем время
    start_time = time.time()
    
    # АНАЛИЗИРУЕМ
    results = analyze_matches_fast(SAMPLE_MATCHES)
    
    # Измеряем время
    elapsed = time.time() - start_time
    
    # Выводим результаты
    print_results(results)
    
    print()
    print("=" * 80)
    print(f"ВРЕМЯ АНАЛИЗА: {elapsed:.2f} сек")
    print(f"Скорость: {len(SAMPLE_MATCHES) / elapsed:.1f} матчей в секунду")
    print("=" * 80)
    print()
    
    print("МАСШТАБИРОВАНИЕ:")
    print(f"  • 10 матчей: ~{10 * (elapsed / len(SAMPLE_MATCHES)):.2f} сек")
    print(f"  • 20 матчей: ~{20 * (elapsed / len(SAMPLE_MATCHES)):.2f} сек")
    print(f"  • 50 матчей: ~{50 * (elapsed / len(SAMPLE_MATCHES)):.2f} сек")
    print()

