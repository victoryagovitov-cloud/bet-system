# -*- coding: utf-8 -*-
"""
📤 ОТПРАВКА ДНЕВНОГО ОТЧЕТА В TELEGRAM

Автоматически отправляет итоги дня в канал
"""
from daily_stats_generator import DailyStatsGenerator
from result_checker import ResultChecker
import requests
import urllib3
import json
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Загружаем конфиг
with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

BOT_TOKEN = CONFIG['notifications']['telegram']['bot_token']
CHANNEL = CONFIG['notifications']['telegram']['channel_username']

def send_daily_report_to_telegram(date=None):
    """
    Отправляет дневной отчет в Telegram
    
    Args:
        date: Дата в формате 'YYYY-MM-DD' (если None - за сегодня)
    """
    print("="*70)
    print("📊 ПОДГОТОВКА ДНЕВНОГО ОТЧЕТА")
    print("="*70 + "\n")
    
    # ШАГ 1: Проверяем все незавершенные прогнозы
    print("🔍 ШАГ 1: Проверка результатов прогнозов\n")
    checker = ResultChecker()
    checker.check_today_predictions()
    
    # ШАГ 2: Генерируем отчет
    print("\n📊 ШАГ 2: Генерация отчета\n")
    generator = DailyStatsGenerator()
    report = generator.generate_full_report(date)
    
    if "Нет прогнозов" in report:
        print("⚠️ Нет прогнозов за этот день, отчет не отправляем")
        return False
    
    # ШАГ 3: Отправляем в Telegram
    print("📤 ШАГ 3: Отправка в Telegram\n")
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHANNEL,
        'text': report
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10, verify=False)
        response.raise_for_status()
        print(f"✅ Отчет отправлен в {CHANNEL}")
        
        # Сохраняем копию отчета в файл
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        filename = f"daily_report_{date}.txt"
        generator.save_report_to_file(date, filename)
        
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("📊 ОТПРАВКА ДНЕВНОГО ОТЧЕТА")
    print("="*70 + "\n")
    
    send_daily_report_to_telegram()
    
    print("\n" + "="*70)
    print("✅ ЗАВЕРШЕНО")
    print("="*70 + "\n")

