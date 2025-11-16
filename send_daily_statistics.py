# -*- coding: utf-8 -*-
"""
АВТОМАТИЧЕСКАЯ ОТПРАВКА ЕЖЕДНЕВНОЙ СТАТИСТИКИ В TELEGRAM
Запускается вечером (например, в 23:00) для отправки итогов дня
"""
import sys
import io
import json
import os
import certifi
import requests
from datetime import datetime
from statistics_generator import StatisticsGenerator

# Для корректной работы с UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Устанавливаем путь к сертификатам
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['SSL_CERT_FILE'] = certifi.where()

def send_daily_statistics():
    """Отправляет ежедневную статистику в Telegram канал"""
    
    # Читаем конфигурацию
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    bot_token = config['telegram_bot_token']
    channel_username = config['telegram_channel_username']
    
    # Генерируем статистику
    generator = StatisticsGenerator()
    
    print("=" * 60)
    print("📊 ГЕНЕРАЦИЯ ЕЖЕДНЕВНОЙ СТАТИСТИКИ")
    print("=" * 60)
    
    # 1. Генерируем текстовый отчет
    print("\n1️⃣ Генерируем текстовый отчет...")
    text_report = generator.generate_text_report()
    
    # 2. Генерируем инфографику
    print("\n2️⃣ Генерируем инфографику...")
    today = datetime.now().strftime("%Y-%m-%d")
    image_file = f"statistics_{today}.png"
    
    try:
        generator.generate_infographic(output_file=image_file)
        has_image = True
    except Exception as e:
        print(f"⚠️ Не удалось создать инфографику: {e}")
        has_image = False
    
    # 3. Отправляем в Telegram
    print("\n3️⃣ Отправляем в Telegram...")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    data = {
        'chat_id': channel_username,
        'text': text_report,
        'parse_mode': None  # Без разметки
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            print("✅ Текстовый отчет отправлен успешно!")
        else:
            print(f"❌ Ошибка отправки текста: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА при отправке текста: {e}")
    
    # Отправляем изображение (если есть)
    if has_image and os.path.exists(image_file):
        print("\n4️⃣ Отправляем инфографику...")
        
        url_photo = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        
        try:
            with open(image_file, 'rb') as photo:
                files = {'photo': photo}
                data_photo = {
                    'chat_id': channel_username,
                    'caption': '📊 Инфографика за сегодня'
                }
                
                response_photo = requests.post(url_photo, files=files, data=data_photo, timeout=30)
                
                if response_photo.status_code == 200:
                    print("✅ Инфографика отправлена успешно!")
                else:
                    print(f"❌ Ошибка отправки изображения: {response_photo.status_code}")
                    print(response_photo.text)
        
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА при отправке изображения: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ОТПРАВКА СТАТИСТИКИ ЗАВЕРШЕНА")
    print("=" * 60)


if __name__ == "__main__":
    send_daily_statistics()

