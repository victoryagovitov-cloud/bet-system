#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ОБРАБОТЧИК СИГНАЛОВ ОТ AUTOHOTKEY

Получает сигналы от AHK (🎯F) и запускает анализ
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.stdout.reconfigure(encoding='utf-8')

import json
import subprocess
from datetime import datetime
from pathlib import Path

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

# Сигнал от AHK для запуска анализа
AHK_SIGNAL = "🎯F"

# Папка проекта
PROJECT_DIR = Path(__file__).parent

# Основные скрипты
ANALYZER_SCRIPT = PROJECT_DIR / "analyze_and_send_telegram.py"
BROWSER_DATA_SCRIPT = PROJECT_DIR / "get_betboom_data.py"  # Создадим отдельно


# ============================================================================
# ФУНКЦИИ ЛОГИРОВАНИЯ
# ============================================================================

def log_event(event_type, message):
    """Логирует события в файл"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {event_type}: {message}\n"
    
    log_file = PROJECT_DIR / "ahk_trigger.log"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    print(log_entry.strip())


# ============================================================================
# ПОЛУЧЕНИЕ ДАННЫХ ИЗ BETBOOM ЧЕРЕЗ BROWSER MCP
# ============================================================================

def get_betboom_data():
    """
    Получает данные о live-матчах с BetBoom через Browser MCP
    
    Возвращает список матчей с полями:
    - team1, team2, score, league, time, coef_p1, coef_p2
    """
    
    log_event("INFO", "Начинаем получение данных с BetBoom через Browser MCP...")
    
    # Готовые тестовые данные (в реальности здесь будет парсинг через MCP)
    # Для демонстрации используем фиксированные данные
    
    test_matches = [
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
            'team1': 'АЗ Алкмаар',
            'team2': 'ПСВ Эйндховен',
            'score': '0-3',
            'league': 'Нидерланды. Эредивизи',
            'time': '1Т, 29 мин',
            'coef_p1': 60.0,
            'coef_p2': 1.03
        },
        {
            'team1': 'Фрайбург',
            'team2': 'Санкт-Паули',
            'score': '2-1',
            'league': 'Германия. Бундеслига',
            'time': '2Т, 89 мин',
            'coef_p1': 1.50,
            'coef_p2': 4.5
        }
    ]
    
    log_event("SUCCESS", f"Получено {len(test_matches)} матчей с BetBoom")
    return test_matches


# ============================================================================
# ЗАПУСК АНАЛИЗА
# ============================================================================

def run_analysis():
    """
    Запускает полный анализ и отправку в Telegram
    """
    
    log_event("START", "=" * 80)
    log_event("INFO", "Получен сигнал от AutoHotkey - начинаем анализ")
    
    try:
        # 1. Получаем данные с BetBoom
        matches = get_betboom_data()
        
        if not matches:
            log_event("WARNING", "Не найдено live-матчей на BetBoom")
            return False
        
        # 2. Сохраняем данные в файл для передачи анализатору
        temp_data_file = PROJECT_DIR / "temp_matches_data.json"
        with open(temp_data_file, 'w', encoding='utf-8') as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)
        
        log_event("INFO", f"Данные сохранены ({len(matches)} матчей)")
        
        # 3. Запускаем анализатор
        log_event("INFO", "Запускаем analyze_and_send_telegram.py...")
        
        result = subprocess.run(
            [sys.executable, str(ANALYZER_SCRIPT)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=str(PROJECT_DIR)
        )
        
        log_event("INFO", "Анализатор завершил работу")
        
        # 4. Логируем вывод
        if result.stdout:
            log_event("OUTPUT", result.stdout[:500])  # Первые 500 символов
        
        if result.returncode != 0:
            log_event("ERROR", f"Ошибка при выполнении: {result.stderr}")
            return False
        
        log_event("SUCCESS", "Анализ и отправка завершены успешно!")
        log_event("END", "=" * 80)
        return True
        
    except Exception as e:
        log_event("CRITICAL", f"Неожиданная ошибка: {e}")
        return False


# ============================================================================
# МОНИТОРИНГ СИГНАЛОВ (для интеграции с Cursor)
# ============================================================================

def monitor_for_signal():
    """
    Мониторит входящие сигналы от AHK
    Предполагается, что AHK отправляет запросы в Cursor через API
    """
    
    log_event("INFO", "Мониторинг сигналов от AutoHotkey активирован")
    print("\n⏳ Ожидание сигналов от AutoHotkey...")
    print("   Сигнал: 🎯F\n")
    
    # В реальной системе здесь будет:
    # - Слушание сокета/порта
    # - Проверка буфера обмена
    # - Перехват горячих клавиш через pyautogui/keyboard
    # - Или получение запросов через веб-API
    
    # Для демонстрации: просто ждем ввода
    import time
    import threading
    
    def check_input():
        while True:
            try:
                user_input = input()
                if AHK_SIGNAL in user_input or user_input.lower() == 'f':
                    log_event("SIGNAL", f"Получен сигнал от AHK: {user_input}")
                    run_analysis()
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\n\nМониторинг остановлен")
                break
    
    thread = threading.Thread(target=check_input, daemon=True)
    thread.start()
    
    # Основной поток остается активным
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nШкода завершена")


# ============================================================================
# КОМАНДНАЯ СТРОКА
# ============================================================================

def show_help():
    """Показывает справку"""
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║         AHK TRIGGER HANDLER - Обработчик сигналов от AHK      ║
╚════════════════════════════════════════════════════════════════╝

КОМАНДЫ:
  python ahk_trigger_handler.py run      - Запустить анализ сейчас
  python ahk_trigger_handler.py monitor  - Ожидать сигналы от AHK
  python ahk_trigger_handler.py help     - Показать эту справку

ПРИМЕРЫ:
  # Запустить анализ прямо сейчас
  python ahk_trigger_handler.py run

  # Запустить мониторинг (ждать сигналов)
  python ahk_trigger_handler.py monitor

ФАЙЛЫ ЛОГОВ:
  - ahk_trigger.log - полный лог всех событий
  - last_telegram_message.txt - последнее отправленное сообщение
""")


if __name__ == '__main__':
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'run':
            # Запустить анализ сейчас
            run_analysis()
        
        elif command == 'monitor':
            # Ожидать сигналы от AHK
            monitor_for_signal()
        
        elif command == 'help':
            show_help()
        
        else:
            print(f"❌ Неизвестная команда: {command}")
            show_help()
    
    else:
        # По умолчанию - показать справку
        show_help()

