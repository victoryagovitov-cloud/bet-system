# -*- coding: utf-8 -*-
"""
⏰ ПЛАНИРОВЩИК ДНЕВНОГО ОТЧЕТА

Автоматически отправляет отчет в конец дня (23:45 МСК)
"""
import schedule
import time
from datetime import datetime
from send_daily_report import send_daily_report_to_telegram

def send_report_job():
    """Задача для отправки отчета"""
    print("\n" + "="*70)
    print(f"⏰ ЗАПУСК ОТПРАВКИ ДНЕВНОГО ОТЧЕТА: {datetime.now().strftime('%H:%M:%S')}")
    print("="*70 + "\n")
    
    try:
        send_daily_report_to_telegram()
        print("\n✅ Отчет успешно отправлен")
    except Exception as e:
        print(f"\n❌ Ошибка при отправке отчета: {e}")

def main():
    """Запуск планировщика"""
    print("="*70)
    print("⏰ ПЛАНИРОВЩИК ДНЕВНЫХ ОТЧЕТОВ")
    print("="*70)
    print(f"🕐 Текущее время: {datetime.now().strftime('%H:%M:%S')}")
    print(f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}")
    print("\n📋 Расписание:")
    print("   • 23:45 МСК - Отправка дневного отчета")
    print("\n✅ Планировщик запущен. Нажмите Ctrl+C для остановки.\n")
    print("="*70 + "\n")
    
    # Настройка расписания
    schedule.every().day.at("23:45").do(send_report_job)
    
    # Для тестирования - можно раскомментировать:
    # schedule.every(2).minutes.do(send_report_job)  # Каждые 2 минуты
    
    # Основной цикл
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Проверяем каждые 30 секунд
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("⏹️ ПЛАНИРОВЩИК ОСТАНОВЛЕН")
        print("="*70 + "\n")

if __name__ == "__main__":
    main()

