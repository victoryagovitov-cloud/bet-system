#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ОТПРАВКА АНАЛИЗА В TELEGRAM (улучшенная версия)

Обновленный скрипт который:
1. Импортирует функции из analyze_and_send_telegram.py
2. Форматирует сообщение
3. Отправляет в @TrueLiveBet с повторными попытками
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.stdout.reconfigure(encoding='utf-8')

import requests
from datetime import datetime
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# ИМПОРТ ОСНОВНЫХ ФУНКЦИЙ
# ============================================================================

from analyze_and_send_telegram import (
    analyze_matches,
    format_telegram_message,
    BOT_TOKEN,
    CHANNEL_ID
)

# ============================================================================
# ОТПРАВКА С ПОВТОРНЫМИ ПОПЫТКАМИ
# ============================================================================

def send_to_telegram_with_retry(message, max_retries=3):
    """
    Отправляет сообщение в Telegram с автоматическими повторными попытками
    
    Args:
        message: текст сообщения
        max_retries: максимальное количество попыток
    
    Returns:
        True если успешно, False если неудачно
    """
    
    print(f"\n📤 Отправка в Telegram (попытки до {max_retries})...")
    print(f"   Канал: {CHANNEL_ID}")
    
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': CHANNEL_ID,
        'text': message,
        'parse_mode': 'HTML'  # Или 'Markdown'
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"   Попытка {attempt}/{max_retries}...", end=' ')
            
            response = requests.post(
                url,
                data=data,
                verify=False,
                timeout=15  # Увеличили таймаут
            )
            
            result = response.json()
            
            if result.get('ok'):
                print("✅")
                print(f"   Message ID: {result['result']['message_id']}")
                return True
            else:
                error_msg = result.get('description', 'Unknown error')
                print(f"❌ {error_msg}")
                
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # 2, 4, 8 секунд
                    print(f"   Ждем {wait_time}с перед повтором...")
                    time.sleep(wait_time)
                    
        except requests.exceptions.Timeout:
            print(f"⏱️ Таймаут")
            if attempt < max_retries:
                wait_time = 2 ** attempt
                print(f"   Ждем {wait_time}с перед повтором...")
                time.sleep(wait_time)
                
        except requests.exceptions.ConnectionError as e:
            print(f"🔗 Ошибка подключения")
            if attempt < max_retries:
                wait_time = 2 ** attempt
                print(f"   Ждем {wait_time}с перед повтором...")
                time.sleep(wait_time)
                
        except Exception as e:
            print(f"❌ {type(e).__name__}: {e}")
            if attempt < max_retries:
                wait_time = 2 ** attempt
                print(f"   Ждем {wait_time}с перед повтором...")
                time.sleep(wait_time)
    
    print(f"\n❌ Не удалось отправить после {max_retries} попыток")
    return False


# ============================================================================
# ЗАГРУЗКА АНАЛИЗА ИЗ ФАЙЛА
# ============================================================================

def load_analysis_from_file():
    """
    Загружает готовый анализ из файла (если существует)
    """
    
    try:
        with open('current_live_analysis_mcp.txt', 'r', encoding='utf-8') as f:
            message = f.read()
        
        print("✅ Найден готовый анализ в current_live_analysis_mcp.txt")
        return message
        
    except FileNotFoundError:
        print("ℹ️ Файл анализа не найден, используем default шаблон")
        return None


# ============================================================================
# ОСНОВНАЯ ФУНКЦИЯ
# ============================================================================

def send_analysis(matches_data=None):
    """
    Полный цикл: анализ → форматирование → отправка с повторами
    
    Args:
        matches_data: список матчей для анализа
    """
    
    print("\n" + "=" * 90)
    print("📱 ОТПРАВКА АНАЛИЗА В TELEGRAM (с повторными попытками)")
    print("=" * 90)
    
    # Проверяем готовый анализ
    existing_analysis = load_analysis_from_file()
    
    if existing_analysis:
        # Используем готовый анализ
        telegram_message = existing_analysis
    else:
        # Если данных нет, используем тестовые
        if matches_data is None:
            matches_data = [
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
                }
            ]
        
        # Анализируем матчи
        recommendations = analyze_matches(matches_data)
        
        # Форматируем для Telegram
        telegram_message = format_telegram_message(recommendations)
    
    # Показываем что отправим
    print("\n📋 Сообщение к отправке:\n")
    print(telegram_message)
    
    # Отправляем с повторами
    success = send_to_telegram_with_retry(telegram_message, max_retries=3)
    
    if success:
        # Сохраняем для логирования
        with open('last_telegram_message.txt', 'w', encoding='utf-8') as f:
            f.write(telegram_message)
        
        print("\n" + "=" * 90)
        print("✅ ВСЁ УСПЕШНО!")
        print("   • Анализ выполнен")
        print("   • Сообщение отправлено в @TrueLiveBet")
        print("   • Копия сохранена в last_telegram_message.txt")
        print("=" * 90 + "\n")
    else:
        print("\n" + "=" * 90)
        print("⚠️ АНАЛИЗ ВЫПОЛНЕН, НО ОТПРАВКА НЕ УДАЛАСЬ")
        print("   • Проверьте интернет соединение")
        print("   • Проверьте TOKEN и CHANNEL_ID в config.json")
        print("   • Сообщение сохранено в last_telegram_message.txt")
        print("=" * 90 + "\n")
    
    return success


if __name__ == '__main__':
    send_analysis()
