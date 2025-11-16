# -*- coding: utf-8 -*-
"""
Отправка отчета анализа 22:45 МСК в Telegram
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

BOT_TOKEN = config['notifications']['telegram']['bot_token']
CHANNEL = config['notifications']['telegram']['channel_username']

# Читаем отчет
with open('telegram_report_22_45.txt', 'r', encoding='utf-8') as f:
    message = f.read()

# Отправляем сообщение
url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'

payload = {
    'chat_id': CHANNEL,
    'text': message
}

print("=" * 70)
print("📤 ОТПРАВКА ОТЧЕТА В TELEGRAM")
print("=" * 70)
print(f"\n🎯 Канал: {CHANNEL}")
print(f"📝 Размер сообщения: {len(message)} символов\n")

try:
    response = requests.post(url, json=payload, timeout=30)
    
    if response.status_code == 200:
        print("✅ ОТЧЕТ УСПЕШНО ОТПРАВЛЕН В @TrueLiveBet!")
        print(f"   Время отправки: {response.json().get('result', {}).get('date', 'N/A')}")
    else:
        print(f"❌ ОШИБКА ОТПРАВКИ: {response.status_code}")
        print(f"   Ответ: {response.text}")
        
except Exception as e:
    print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    
print("\n" + "=" * 70)
