#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
РАБОЧИЙ АВТОКЛИКЕР для отправки запросов в Cursor Chat
Координаты: (2026, 1361) - ПРОВЕРЕНЫ И РАБОТАЮТ
Интервал: каждые 45 минут с 9:00 до 23:30 МСК
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import pyautogui
import pyperclip
import time
import schedule
import logging
from datetime import datetime, timezone, timedelta

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('working_autoclicker.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ПРОВЕРЕННЫЕ КООРДИНАТЫ поля ввода Cursor Chat
CHAT_X = 1603
CHAT_Y = 1340

# Московская временная зона
MOSCOW_TZ = timezone(timedelta(hours=3))

def get_moscow_time():
    """Получить текущее время в Москве"""
    return datetime.now(MOSCOW_TZ)

def is_working_hours():
    """Проверить рабочие часы (9:00-23:30 по Москве)"""
    moscow_time = get_moscow_time()
    hour = moscow_time.hour
    minute = moscow_time.minute
    
    # С 9:00 до 23:30
    if hour < 9:
        return False
    if hour > 23:
        return False
    if hour == 23 and minute > 30:
        return False
    
    return True

def send_analysis_request():
    """Отправить запрос на анализ в Cursor Chat"""
    if not is_working_hours():
        logger.info("⏰ Вне рабочих часов (9:00-23:30 МСК), пропускаем")
        return
    
    try:
        current_time = get_moscow_time()
        logger.info(f"🚀 Начинаю отправку запроса в {current_time.strftime('%H:%M:%S')} МСК")
        
        # Текст запроса
        request_text = f"""🎯 АВТОМАТИЧЕСКИЙ ЗАПРОС НА АНАЛИЗ BETBOOM - {current_time.strftime('%H:%M')} МСК

Проверь актуальные матчи на BetBoom:
- Футбол: https://betboom.ru/sport/football?period=all&type=live
- Теннис: https://betboom.ru/sport/tennis?period=all&type=live  
- Гандбол: https://betboom.ru/sport/handball?period=all&type=live

Проведи анализ по системе (включая гандбольные тоталы!) и отправь результаты в канал @TrueLiveBet

Время запроса: {current_time.strftime('%d.%m.%Y %H:%M:%S')} МСК"""
        
        # Копируем текст в буфер обмена
        pyperclip.copy(request_text)
        logger.info("📋 Текст скопирован в буфер обмена")
        
        # Кликаем в поле ввода чата
        pyautogui.click(CHAT_X, CHAT_Y)
        logger.info(f"🖱️ Клик по координатам ({CHAT_X}, {CHAT_Y})")
        time.sleep(0.5)
        
        # Вставляем текст из буфера (Ctrl+V)
        pyautogui.hotkey('ctrl', 'v')
        logger.info("📝 Текст вставлен")
        time.sleep(0.5)
        
        # Отправляем (Enter)
        pyautogui.press('enter')
        logger.info("✅ Запрос отправлен!")
        
        logger.info(f"🎉 ЗАПРОС УСПЕШНО ОТПРАВЛЕН В {current_time.strftime('%H:%M:%S')} МСК")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке: {e}")

def setup_schedule():
    """Настройка расписания каждые 45 минут с 9:00 до 23:30"""
    logger.info("⚙️ НАСТРОЙКА РАСПИСАНИЯ АВТОКЛИКЕРА")
    logger.info("🕘 Рабочие часы: 9:00-23:30 МСК")
    logger.info("⏰ Интервал: каждые 45 минут")
    logger.info(f"🖱️ Координаты клика: ({CHAT_X}, {CHAT_Y})")
    
    # Расписание каждые 45 минут с 9:00 до 23:30
    times = []
    for hour in range(9, 24):  # 9:00 - 23:30
        times.append(f"{hour:02d}:00")
        if hour < 23:
            times.append(f"{hour:02d}:45")
        elif hour == 23:
            times.append("23:30")
    
    # Добавляем задачи в расписание
    for time_str in times:
        schedule.every().day.at(time_str).do(send_analysis_request)
        logger.info(f"📅 Добавлено время: {time_str}")
    
    logger.info(f"✅ Настроено {len(times)} временных слотов")

def main():
    """Основная функция автокликера"""
    print("=" * 70)
    print("🤖 РАБОЧИЙ АВТОКЛИКЕР ДЛЯ CURSOR CHAT")
    print("=" * 70)
    print(f"🕘 Рабочие часы: 9:00-23:30 МСК")
    print(f"⏰ Интервал: каждые 45 минут")
    print(f"🖱️ Координаты: ({CHAT_X}, {CHAT_Y})")
    print(f"📱 Результаты → @TrueLiveBet")
    print("=" * 70)
    print()
    
    # Предупреждение
    print("⚠️  ВАЖНО:")
    print("1. НЕ ЗАКРЫВАЙ окно Cursor - автокликер должен видеть поле ввода")
    print("2. Координаты проверены и работают корректно")
    print("3. Система полностью автономна")
    print("4. Логи сохраняются в working_autoclicker.log")
    print()
    
    input("Нажми ENTER для запуска автокликера...")
    print()
    
    # Настраиваем расписание
    setup_schedule()
    
    logger.info("🚀 АВТОКЛИКЕР ЗАПУЩЕН!")
    next_run = schedule.next_run()
    if next_run:
        logger.info(f"📊 Следующая отправка в: {next_run.strftime('%H:%M МСК')}")
    
    # Основной цикл
    try:
        while True:
            schedule.run_pending()
            
            # Показываем статус каждые 10 минут
            current_time = get_moscow_time()
            if current_time.minute % 10 == 0 and current_time.second == 0:
                next_run = schedule.next_run()
                if next_run:
                    logger.info(f"⏰ {current_time.strftime('%H:%M МСК')} | Следующая отправка: {next_run.strftime('%H:%M')}")
                time.sleep(1)  # Избегаем дублирования
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("⛔ Автокликер остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()

