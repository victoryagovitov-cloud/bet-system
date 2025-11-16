#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ФОНОВЫЙ СЕРВИС - ПОЛНОСТЬЮ АВТОНОМНЫЙ

Этот скрипт:
1. Запускается один раз и работает в фоне
2. Каждые 45 минут (9:00-23:30 МСК) автоматически запускает анализ
3. НЕ требует участия пользователя
4. НЕ требует дополнительных команд
5. Просто отправляет результаты в @TrueLiveBet

ИНСТРУКЦИЯ:
  1. Запусти один раз: python background_service.py
  2. Закрой консоль/оставь в фоне
  3. Система сама будет работать по расписанию
  4. Результаты будут появляться в @TrueLiveBet каждые 45 минут
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.stdout.reconfigure(encoding='utf-8')

import time
import json
from datetime import datetime
from pathlib import Path
from analyze_and_send_telegram import (
    analyze_matches,
    format_telegram_message,
    send_to_telegram
)
from get_betboom_data import get_betboom_data

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

PROJECT_DIR = Path(__file__).parent
LOG_FILE = PROJECT_DIR / "background_service.log"

# Расписание (в минутах)
INTERVAL_MINUTES = 45
START_HOUR = 9
END_HOUR = 23

# ============================================================================
# ЛОГИРОВАНИЕ
# ============================================================================

def log_event(message, level="INFO"):
    """Логирует событие в файл и консоль"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {level}: {message}"
    
    print(log_entry)
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    except:
        pass


# ============================================================================
# ПРОВЕРКА ВРЕМЕНИ
# ============================================================================

def is_working_hours():
    """Проверяет находимся ли мы в рабочее время (9:00-23:30 МСК)"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    
    # Рабочее время: 9:00 - 23:30
    if hour < START_HOUR:
        return False
    if hour >= END_HOUR and minute > 30:
        return False
    
    return True


def get_next_run_time():
    """Вычисляет когда будет следующий запуск"""
    now = datetime.now()
    
    # Если сейчас не рабочее время
    if not is_working_hours():
        # Следующий запуск завтра в 9:00
        from datetime import timedelta
        next_run = now.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)
        return next_run
    
    # Вычисляем следующий запуск на основе интервала
    minutes_since_start = (now.hour - START_HOUR) * 60 + now.minute
    minutes_until_next = INTERVAL_MINUTES - (minutes_since_start % INTERVAL_MINUTES)
    
    from datetime import timedelta
    next_run = now + timedelta(minutes=minutes_until_next)
    
    return next_run


# ============================================================================
# ЗАПУСК АНАЛИЗА
# ============================================================================

def run_analysis_cycle():
    """
    Выполняет один цикл анализа:
    1. Получает данные с BetBoom
    2. Анализирует матчи
    3. Форматирует сообщение
    4. Отправляет в @TrueLiveBet
    """
    
    try:
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_event(f"▶️ ЦИКЛ АНАЛИЗА #{datetime.now().strftime('%Y-%m-%d %H:%M')}", "RUN")
        
        # Шаг 1: Получаем данные
        log_event("1️⃣ Получение данных с BetBoom...", "INFO")
        matches_data = get_betboom_data()
        
        if not matches_data:
            log_event("❌ Ошибка: не удалось получить данные", "ERROR")
            return False
        
        log_event(f"   ✓ Получено {len(matches_data)} матчей", "INFO")
        
        # Шаг 2: Анализируем
        log_event("2️⃣ Анализ матчей...", "INFO")
        recommendations = analyze_matches(matches_data)
        log_event(f"   ✓ Найдено {len(recommendations)} подходящих матчей", "INFO")
        
        # Шаг 3: Форматируем
        log_event("3️⃣ Форматирование сообщения...", "INFO")
        message = format_telegram_message(recommendations)
        log_event(f"   ✓ Сообщение готово ({len(message)} символов)", "INFO")
        
        # Шаг 4: Отправляем
        log_event("4️⃣ Отправка в @TrueLiveBet...", "INFO")
        success = send_to_telegram(message)
        
        if success:
            log_event("✅ ЦИКЛ ЗАВЕРШЕН УСПЕШНО!", "SUCCESS")
            log_event(f"   📊 Матчей анализировано: {len(matches_data)}", "INFO")
            log_event(f"   ✓ Рекомендаций отправлено: {len(recommendations)}", "INFO")
            return True
        else:
            log_event("⚠️ ОШИБКА ОТПРАВКИ - попытка повтора...", "WARNING")
            # Повторная попытка через 30 сек
            time.sleep(30)
            success = send_to_telegram(message)
            if success:
                log_event("✅ ПОВТОРНАЯ ОТПРАВКА УСПЕШНА", "SUCCESS")
                return True
            else:
                log_event("❌ ПОВТОРНАЯ ОТПРАВКА НЕ УДАЛАСЬ", "ERROR")
                return False
    
    except Exception as e:
        log_event(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}", "CRITICAL")
        import traceback
        log_event(traceback.format_exc(), "ERROR")
        return False


# ============================================================================
# ГЛАВНЫЙ ЦИКЛ СЕРВИСА
# ============================================================================

def start_service():
    """
    Главный цикл сервиса:
    1. Проверяет время
    2. Если рабочее время - запускает анализ
    3. Ждет до следующего запуска
    4. Повторяет
    """
    
    log_event("=" * 80, "")
    log_event("🚀 ФОНОВЫЙ СЕРВИС ЗАПУЩЕН", "START")
    log_event("=" * 80, "")
    log_event(f"Рабочее время: {START_HOUR}:00 - {END_HOUR}:30 МСК", "INFO")
    log_event(f"Интервал между запусками: {INTERVAL_MINUTES} минут", "INFO")
    log_event("Сервис готов к автоматическому анализу", "INFO")
    log_event("=" * 80, "")
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║         ✅ ФОНОВЫЙ СЕРВИС АКТИВИРОВАН                         ║
║                                                                ║
║  Система будет автоматически:                                 ║
║  • Каждые 45 минут (9:00-23:30 МСК)                           ║
║  • Запускать анализ live-матчей                               ║
║  • Отправлять результаты в @TrueLiveBet                       ║
║                                                                ║
║  🔔 Результаты будут видны в канале                           ║
║  📋 Логи в файле: background_service.log                      ║
║                                                                ║
║  ⛔ Для остановки: Ctrl+C                                      ║
╚════════════════════════════════════════════════════════════════╝
""")
    
    run_count = 0
    last_run = None
    
    try:
        while True:
            now = datetime.now()
            
            # Проверяем если уже пора запускать
            if last_run is None or (now - last_run).total_seconds() >= INTERVAL_MINUTES * 60:
                
                # Дополнительная проверка рабочего времени
                if is_working_hours():
                    run_count += 1
                    log_event("", "")
                    log_event(f"⏰ Времени пришло! Запуск анализа #{run_count}", "SCHEDULE")
                    
                    # Запускаем анализ
                    success = run_analysis_cycle()
                    last_run = now
                    
                    # Вычисляем следующий запуск
                    next_run = get_next_run_time()
                    minutes_until = int((next_run - now).total_seconds() / 60)
                    log_event(f"⏳ Следующий запуск: {next_run.strftime('%H:%M:%S')} (через {minutes_until} минут)", "INFO")
                    log_event("", "")
                
                else:
                    # Сейчас не рабочее время
                    next_run = get_next_run_time()
                    log_event(f"⏸️ Не рабочее время. Следующий запуск завтра в {next_run.strftime('%H:%M:%S')}", "INFO")
            
            # Спим 1 минуту перед следующей проверкой
            time.sleep(60)
    
    except KeyboardInterrupt:
        log_event("", "")
        log_event("⛔ СЕРВИС ОСТАНОВЛЕН (Ctrl+C)", "STOP")
        log_event(f"Выполнено циклов: {run_count}", "INFO")
        log_event("=" * 80, "")
        print("\n⛔ Сервис остановлен\n")


# ============================================================================
# ИНФОРМАЦИЯ И СПРАВКА
# ============================================================================

def show_banner():
    """Показывает информацию о сервисе"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║          ФОНОВЫЙ СЕРВИС АНАЛИЗА LIVE-СТАВОК                   ║
║                                                                ║
║  Автоматический запуск каждые 45 минут (9:00-23:30 МСК)      ║
╚════════════════════════════════════════════════════════════════╝

📋 ИНСТРУКЦИЯ:

  1. Запусти этот скрипт один раз:
     python background_service.py
  
  2. Окно консоли можно оставить открытым или свернуть
  
  3. Система будет автоматически:
     ✓ Проверять время каждую минуту
     ✓ Запускать анализ каждые 45 минут
     ✓ Отправлять результаты в @TrueLiveBet
     ✓ Логировать все события
  
  4. Для остановки: нажми Ctrl+C в консоли

📊 ЧТО ПРОИСХОДИТ:

  9:00 МСК  → Первый запуск анализа
  9:45 МСК  → Второй запуск
  10:30 МСК → Третий запуск
  ...
  23:30 МСК → Последний запуск дня
  23:31+    → Система ждет до 9:00 следующего дня

📝 ЛОГИРОВАНИЕ:

  Все события сохраняются в: background_service.log
  
  Можешь открыть файл и видеть:
  ✓ Когда запускался анализ
  ✓ Сколько матчей было обработано
  ✓ Сколько рекомендаций отправлено
  ✓ Все ошибки (если были)

🎯 РЕЗУЛЬТАТЫ:

  Каждый анализ → сообщение в @TrueLiveBet
  Подписчики видят рекомендации сразу после запуска
  Никаких задержек, всё автоматическое!

""")


# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

if __name__ == '__main__':
    
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'help':
        show_banner()
    else:
        # Запуск сервиса
        show_banner()
        print("\n🚀 Запуск сервиса...\n")
        start_service()

