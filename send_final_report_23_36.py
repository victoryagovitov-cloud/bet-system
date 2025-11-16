# -*- coding: utf-8 -*-
"""
Отправка финального отчета 23:36 МСК в Telegram
"""
import sys
import io
import requests
import json
import certifi
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Устанавливаем правильный путь к TLS сертификатам
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['SSL_CERT_FILE'] = certifi.where()

# Загружаем конфигурацию
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

bot_token = config['notifications']['telegram']['bot_token']
channel_username = config['notifications']['telegram']['channel_username']

# Читаем отчет
with open('telegram_report_final_23_36.txt', 'r', encoding='utf-8') as f:
    message = f.read()

# Отправляем сообщение
url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
data = {
    'chat_id': channel_username,
    'text': message
}

try:
    response = requests.post(url, json=data, verify=certifi.where())
    
    if response.status_code == 200:
        print("✅ ФИНАЛЬНЫЙ ОТЧЕТ УСПЕШНО ОТПРАВЛЕН В TELEGRAM!")
        print(f"📱 Канал: {channel_username}")
        print(f"⏰ Время: 23:36 МСК")
        print(f"⚽ Найдено: 1 подходящий матч (Депортиво Кали Ж)")
    else:
        print(f"❌ ОШИБКА: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")

