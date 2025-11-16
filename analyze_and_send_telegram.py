#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПОЛНАЯ ИНТЕГРАЦИЯ: АНАЛИЗ + ОТПРАВКА В TELEGRAM

Шаг 1: Анализирует матчи (через Browser MCP или готовые данные)
Шаг 2: Форматирует сообщение для Telegram
Шаг 3: Отправляет результаты в @TrueLiveBet
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.stdout.reconfigure(encoding='utf-8')

import requests
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Импортируем ТОЛЬКО Browser MCP версию
from get_betboom_browser_mcp_only import get_betboom_data

# ============================================================================
# КОНФИГУРАЦИЯ TELEGRAM
# ============================================================================

BOT_TOKEN = '7824400107:AAGZqPdS0E0N3HsYpD8TW9m8c-bapFd-RHk'
CHANNEL_ID = '@TrueLiveBet'

# ============================================================================
# ФУНКЦИЯ АНАЛИЗА (из analyzer_with_justification.py)
# ============================================================================

def format_justification(result):
    """Формирует обоснование для матча"""
    
    favorite = result['favorite']
    score = result['score']
    coef = result['favorite_coef']
    
    if result['recommendation'] == 'ПРИНЯТЬ':
        # Определяем насколько уверены
        if coef < 1.2:
            emoji = "🔥"
        elif coef < 1.5:
            emoji = "✓"
        else:
            emoji = "💪"
        
        justification = f"""  • {favorite} - фаворит ({emoji} кэф {coef:.2f})
  • На поле контролирует (счет {score})"""
    else:
        justification = """  • Фаворит не подтвердил статус
  • На поле ведет аутсайдер"""
    
    return justification


def analyze_matches(matches_data):
    """
    Анализирует матчи и возвращает список рекомендаций
    """
    
    print("\n📊 Начало анализа матчей...")
    print(f"Всего матчей к проверке: {len(matches_data)}\n")
    
    recommendations = []
    
    for idx, match_data in enumerate(matches_data, 1):
        # Парсим счет
        score_parts = match_data['score'].split('-')
        score1 = int(score_parts[0])
        score2 = int(score_parts[1])
        
        # Проверка: матч не ничейный?
        if score1 == score2:
            print(f"⚪ Матч {idx}: {match_data['team1']} vs {match_data['team2']} - НИЧЬЯ, пропускаем")
            continue
        
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
            is_p1_leader = True
        elif score2 > score1:
            leader = match_data['team2']
            is_p1_leader = False
        else:
            leader = None
            is_p1_leader = None
        
        # 3. Проверяем: ведет ли фаворит?
        favorite_leads = (is_p1_favorite == is_p1_leader) and leader is not None
        
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
            'favorite_leads': favorite_leads,
            'recommendation': 'ПРИНЯТЬ' if favorite_leads else 'ОТКЛОНИТЬ'
        }
        
        # 5. Добавляем в рекомендации если подходит
        if favorite_leads:
            recommendations.append(result)
            print(f"✅ Матч {idx}: {match_data['team1']} vs {match_data['team2']} - ПОДХОДИТ")
        else:
            print(f"❌ Матч {idx}: {match_data['team1']} vs {match_data['team2']} - не подходит")
    
    print(f"\n📈 Результаты: {len(recommendations)} подходящих матчей из {len(matches_data)}\n")
    return recommendations


# ============================================================================
# ФУНКЦИЯ ФОРМАТИРОВАНИЯ ДЛЯ TELEGRAM
# ============================================================================

def format_telegram_message(recommendations):
    """
    Форматирует рекомендации в красивое сообщение для Telegram
    Следует шаблону из CRITICAL_INSTRUCTIONS.md
    """
    
    current_time = datetime.now().strftime('%H:%M')
    current_date = datetime.now().strftime('%d.%m.%Y')
    
    if not recommendations:
        # Нет подходящих матчей
        message = f"""🎯 LIVE-АНАЛИЗ • {current_time} МСК, {current_date}

—————————————

⚠️ В данный момент подходящих матчей для рекомендации не найдено.

Следующий анализ через 45 минут.

—————————————

🤝 @TrueLiveBet — честный ИИ-анализ лайв-ставок"""
        
        return message
    
    # Есть рекомендации
    message = f"""🎯 LIVE-АНАЛИЗ • {current_time} МСК, {current_date}

—————————————

⚽ ФУТБОЛ ⚽

"""
    
    for i, rec in enumerate(recommendations, 1):
        message += f"""{i}. {rec['team1']} vs {rec['team2']}

   Счет: {rec['score']} ({rec['time']}) | {rec['league']}

   🎯 Рекомендуем: {rec['favorite']}

   📊 Обоснование:
{format_justification(rec)}

   💰 Кэф BetBoom: ~{rec['favorite_coef']:.2f}

"""
    
    message += """—————————————

📌 Важные моменты:
  • Все рекомендации основаны на анализе лайв-данных
  • Ставим только на матчи где фаворит лидирует
  • Размер ставки - только из собственного банка

—————————————

⚠️ Дисклеймер: Беттинг связан с рисками. Анализируйте самостоятельно перед ставкой.

🤝 @TrueLiveBet — честный ИИ-анализ лайв-ставок
"""
    
    return message


# ============================================================================
# ФУНКЦИЯ ОТПРАВКИ В TELEGRAM
# ============================================================================

def send_to_telegram(message):
    """
    Отправляет сообщение в канал @TrueLiveBet
    """
    
    print("\n📤 Подготовка отправки в Telegram...")
    print(f"Канал: {CHANNEL_ID}")
    
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': CHANNEL_ID,
        'text': message
    }
    
    try:
        response = requests.post(url, data=data, verify=False, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            print(f"\n✅ СООБЩЕНИЕ УСПЕШНО ОТПРАВЛЕНО!")
            print(f"Message ID: {result['result']['message_id']}")
            return True
        else:
            print(f"\n❌ Ошибка Telegram: {result}")
            return False
            
    except Exception as e:
        print(f"\n❌ Ошибка подключения: {e}")
        return False


# ============================================================================
# ОСНОВНАЯ ФУНКЦИЯ
# ============================================================================

def main(matches_data=None):
    """
    Главная функция: анализ → форматирование → отправка
    
    ТОЛЬКО Browser MCP - никаких fallback!
    """
    
    print("\n" + "=" * 90)
    print("🚀 АНАЛИЗ + TELEGRAM (ТОЛЬКО BROWSER MCP)")
    print("=" * 90)
    
    # Получаем данные ТОЛЬКО через Browser MCP
    if matches_data is None:
        matches_data = get_betboom_data()
    
    # ШАГ 1: Анализируем матчи
    recommendations = analyze_matches(matches_data)
    
    # ШАГ 2: Форматируем для Telegram
    telegram_message = format_telegram_message(recommendations)
    
    # ШАГ 3: Показываем что отправим
    print("\n📋 Сообщение для отправки:\n")
    print(telegram_message)
    
    # ШАГ 4: Отправляем в Telegram
    success = send_to_telegram(telegram_message)
    
    if success:
        # Сохраняем для логирования
        with open('last_telegram_message.txt', 'w', encoding='utf-8') as f:
            f.write(telegram_message)
        print("\n✅ Анализ завершен и отправлен в @TrueLiveBet!")
    else:
        print("\n⚠️ Анализ завершен, но не удалось отправить в Telegram")
    
    print("=" * 90 + "\n")




if __name__ == '__main__':
    main()

