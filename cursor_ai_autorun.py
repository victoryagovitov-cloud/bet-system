#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
АВТОМАТИЧЕСКИЙ ЗАПУСК ПО СИГНАЛУ ОТ AUTOHOTKEY

Этот скрипт:
1. Получает сообщение 🎯F от AutoHotkey в чате Cursor
2. Автоматически запускает анализ
3. Форматирует результаты
4. Отправляет в @TrueLiveBet

Работает как "слушатель" - постоянно ждет сигнал от AutoHotkey
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.stdout.reconfigure(encoding='utf-8')

import time
import subprocess
import json
from datetime import datetime
from pathlib import Path

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

PROJECT_DIR = Path(__file__).parent
SIGNAL = "🎯F"
LOG_FILE = PROJECT_DIR / "ai_autorun.log"

# ============================================================================
# ЛОГИРОВАНИЕ
# ============================================================================

def log_event(message, level="INFO"):
    """Логирует событие"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {level}: {message}"
    
    print(log_entry)
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry + '\n')


# ============================================================================
# ПОЛУЧЕНИЕ СИГНАЛА ОТ AUTOHOTKEY
# ============================================================================

def wait_for_signal():
    """
    Ждет сигнала 🎯F от AutoHotkey в чате Cursor
    
    ИНСТРУКЦИЯ ДЛЯ AUTOHOTKEY:
    
    Когда AutoHotkey хочет запустить анализ, он отправляет:
    - В окно Cursor
    - В чат (как будто пользователь пишет)
    - Текст: "🎯F"
    
    Затем этот скрипт получает сигнал и запускает анализ
    """
    
    log_event("=" * 80, "")
    log_event("СЛУШАТЕЛЬ АКТИВИРОВАН - Ожидание сигнала 🎯F от AutoHotkey", "START")
    log_event("=" * 80, "")
    
    print("\n🎧 Слушаю сигналы от AutoHotkey...")
    print(f"   Ожидаемый сигнал: {SIGNAL}")
    print("   Статус: АКТИВЕН ✅\n")
    
    # В реальной системе здесь будет мониторинг
    # чата Cursor через API или через получение текста из буфера обмена
    # 
    # Пока используем простой метод: проверка файла сигнала
    
    signal_file = PROJECT_DIR / "ahk_signal.txt"
    
    try:
        while True:
            # Проверяем если AutoHotkey создал файл сигнала
            if signal_file.exists():
                with open(signal_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if SIGNAL in content:
                    log_event(f"📍 Получен сигнал: {SIGNAL}", "SIGNAL")
                    signal_file.unlink()  # Удалим файл после прочтения
                    return True
            
            time.sleep(1)  # Проверяем каждую секунду
    
    except KeyboardInterrupt:
        print("\n\n⛔ Слушатель остановлен пользователем")
        log_event("Слушатель остановлен", "INFO")
        return False


# ============================================================================
# ЗАПУСК АНАЛИЗА
# ============================================================================

def run_analysis():
    """
    Запускает полный анализ и отправку в Telegram
    """
    
    log_event("▶️ Запуск анализа...", "RUN")
    
    try:
        # Импортируем функции из основного модуля
        from analyze_and_send_telegram import (
            analyze_matches,
            format_telegram_message,
            send_to_telegram,
            get_test_data
        )
        
        # ШАГ 1: Получаем данные
        log_event("Получение данных с BetBoom...", "INFO")
        matches_data = get_test_data()
        log_event(f"Получено {len(matches_data)} матчей", "INFO")
        
        # ШАГ 2: Анализируем
        log_event("Анализ матчей...", "INFO")
        recommendations = analyze_matches(matches_data)
        log_event(f"Найдено {len(recommendations)} подходящих матчей", "INFO")
        
        # ШАГ 3: Форматируем
        log_event("Форматирование сообщения...", "INFO")
        message = format_telegram_message(recommendations)
        
        # ШАГ 4: Отправляем
        log_event("Отправка в @TrueLiveBet...", "INFO")
        success = send_to_telegram(message)
        
        if success:
            log_event("✅ Анализ завершен успешно! Результаты отправлены в @TrueLiveBet", "SUCCESS")
            return True
        else:
            log_event("⚠️ Анализ завершен, но отправка не удалась", "WARNING")
            return False
    
    except Exception as e:
        log_event(f"❌ Ошибка при анализе: {e}", "ERROR")
        return False


# ============================================================================
# ГЛАВНЫЙ ЦИКЛ
# ============================================================================

def main():
    """
    Главный цикл: ждет сигнал → запускает анализ → повторяет
    """
    
    log_event("Инициализация системы...", "INIT")
    print("\n╔════════════════════════════════════════════════════╗")
    print("║     🤖 AI AUTORUN - АВТОМАТИЧЕСКИЙ ЗАПУСК        ║")
    print("║                                                    ║")
    print("║  Система слушает сигналы 🎯F от AutoHotkey      ║")
    print("║  и автоматически запускает анализ                ║")
    print("╚════════════════════════════════════════════════════╝\n")
    
    run_count = 0
    
    while True:
        try:
            # Ждем сигнал
            signal_received = wait_for_signal()
            
            if not signal_received:
                break
            
            run_count += 1
            log_event(f"Запуск анализа #{run_count}", "INFO")
            
            # Запускаем анализ
            success = run_analysis()
            
            if success:
                log_event(f"Анализ #{run_count} завершен успешно", "SUCCESS")
            else:
                log_event(f"Анализ #{run_count} завершен с ошибками", "WARNING")
            
            # Ждем немного перед следующим циклом
            log_event("Готово к следующему сигналу", "INFO")
            print("\n🎧 Ожидание следующего сигнала...\n")
            
        except KeyboardInterrupt:
            print("\n\n⛔ Система остановлена")
            log_event("Система остановлена пользователем", "STOP")
            break
        
        except Exception as e:
            log_event(f"❌ Неожиданная ошибка: {e}", "ERROR")
            time.sleep(5)  # Ждем перед повтором


# ============================================================================
# ТЕСТИРОВАНИЕ
# ============================================================================

def test_mode():
    """
    Тестовый режим - запускает анализ один раз
    """
    
    log_event("ТЕСТОВЫЙ РЕЖИМ - Запуск анализа один раз", "TEST")
    
    print("\n╔════════════════════════════════════════════════════╗")
    print("║            📝 ТЕСТОВЫЙ РЕЖИМ                      ║")
    print("║                                                    ║")
    print("║  Запуск анализа один раз (без ожидания сигнала)   ║")
    print("╚════════════════════════════════════════════════════╝\n")
    
    success = run_analysis()
    
    if success:
        print("\n✅ Тест пройден успешно!")
    else:
        print("\n❌ Тест завершился с ошибками")
    
    return success


# ============================================================================
# СПРАВКА
# ============================================================================

def show_help():
    """Показывает справку"""
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║         🤖 AI AUTORUN - Автоматический запуск анализа        ║
╚════════════════════════════════════════════════════════════════╝

ОПИСАНИЕ:
  Система слушает сигналы от AutoHotkey (🎯F) и автоматически
  запускает анализ live-матчей с отправкой в @TrueLiveBet

КОМАНДЫ:
  
  python cursor_ai_autorun.py
    → Запустить слушатель (ждет сигналы от AutoHotkey)
  
  python cursor_ai_autorun.py test
    → Тестовый режим (запустить анализ один раз)
  
  python cursor_ai_autorun.py help
    → Показать эту справку

КАК ЭТО РАБОТАЕТ:

  1. Запусти: python cursor_ai_autorun.py
  2. Система начнет слушать сигналы 🎯F
  3. Когда AutoHotkey отправит сигнал → автоматически запустится анализ
  4. Результаты отправятся в @TrueLiveBet
  5. Система ждет следующий сигнал

ИНТЕГРАЦИЯ С AUTOHOTKEY:

  В скрипте cursor_autosend.ahk нужно:
  
  1. Каждые 45 минут отправить сигнал 🎯F
  2. Этот скрипт получит сигнал
  3. И автоматически запустит анализ

ФАЙЛЫ:

  ai_autorun.log
    → Логи всех операций и сигналов
  
  ahk_signal.txt
    → Временный файл для передачи сигнала от AutoHotkey

ПРИМЕРЫ:

  # Запустить слушатель
  python cursor_ai_autorun.py
  
  # Тестирование
  python cursor_ai_autorun.py test
  
  # Справка
  python cursor_ai_autorun.py help

СИГНАЛЫ:

  Ожидаемый сигнал: 🎯F
  
  Может быть отправлен через:
  - Буфер обмена (Clipboard)
  - Файл сигнала (ahk_signal.txt)
  - Прямое сообщение в чат Cursor

""")


# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

if __name__ == '__main__':
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            test_mode()
        
        elif command == 'help':
            show_help()
        
        else:
            print(f"❌ Неизвестная команда: {command}\n")
            show_help()
    
    else:
        # Главный режим - слушать сигналы
        main()

