# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Загружаем конфиг
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

current_time = datetime.now().strftime('%H:%M')
current_date = datetime.now().strftime('%d.%m.%Y')

message = f"""🎯 LIVE-АНАЛИЗ • {current_time} МСК, {current_date}

—————————————

⚽ ФУТБОЛ ⚽

—————————————

1️⃣ Енисей - Черноморец
   Россия. 1-я лига

   Счет: 1:0 (2Т, 73 мин)
   Рекомендация: П1 - коэф. 1.2

   📌 Енисей уверенно контролирует матч. Счет 1:0 в пользу фаворита. Высокие шансы на удержание результата.

   ✅ ИДЕАЛЬНЫЙ ⭐⭐⭐⭐

—————————————

🔥 @TrueLiveBet | Честные прогнозы с ИИ

⚠️ Ставки — это риск. Играйте ответственно и в рамках своих возможностей."""

# Отправляем сообщение
url = f"https://api.telegram.org/bot{config['notifications']['telegram']['bot_token']}/sendMessage"
data = {
    'chat_id': config['notifications']['telegram']['channel_username'],
    'text': message
}

try:
    response = requests.post(url, data=data, verify=False, timeout=10)
    result = response.json()
    
    if result.get('ok'):
        print("Сообщение успешно отправлено в канал @TrueLiveBet")
        print(f"Время: {current_time} МСК, {current_date}")
        print("Найдено подходящих матчей: 1")
        print("\nМАТЧ:")
        print("- Енисей 1:0 Черноморец (П1: 1.2) ИДЕАЛЬНЫЙ")
    else:
        print(f"Ошибка отправки: {result}")
        
except Exception as e:
    print(f"Ошибка при отправке: {e}")

