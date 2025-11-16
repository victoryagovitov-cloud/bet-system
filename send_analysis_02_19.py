# -*- coding: utf-8 -*-
import requests
import json
import urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

BOT_TOKEN = CONFIG['notifications']['telegram']['bot_token']
CHANNEL = CONFIG['notifications']['telegram']['channel_username']

message = """───────────────────────────────────
📊 АНАЛИЗ LIVE-МАТЧЕЙ НА 02:19 МСК (28.10.2025)

⚽ ФУТБОЛ:

1️⃣ Шапекоэнсе - Операрио ПР
   Бразилия. Серия B
   
   Счет: 2:0 (2Т, 60 мин)
   
   Рекомендация: П1 - коэф. 1.03 🔒
   
   📌 Анализ:
   - Фаворит ведет 2:0 на 60-й минуте
   - Матч практически завершен
   - Минимальный риск
   
   Источник: BetBoom live
   
   ✅ Категория: МЕРТВЫЙ ⭐⭐⭐⭐⭐

---

🎾 ТЕННИС:

1️⃣ Лизаразо Ю. - Перес Гарсия М.П.
   WTA 125. Кали. Грунт. Колумбия
   
   Счет: 3:0 в геймах (1-й сет)
   
   Рекомендация: П1 - коэф. 1.04 🔒
   
   📌 Анализ:
   - Лизаразо уверенно ведет 3:0
   - Полный контроль первого сета
   - Минимальный риск
   
   Источник: BetBoom live
   
   ✅ Категория: МЕРТВЫЙ ⭐⭐⭐⭐⭐

---

2️⃣ Папамихаил/Риера - Себальос/Золотарева
   WTA 125. Кали. Грунт. Пары
   
   Счет: 1:0, 5:4 во 2-м сете (15:30)
   
   Рекомендация: П1 - коэф. 1.12
   
   📌 Анализ:
   - Выиграли 1-й сет
   - Ведут 5:4 во 2-м сете
   - Контролируют матч
   
   Источник: BetBoom live
   
   ✅ Категория: ОТЛИЧНЫЙ ⭐⭐⭐

---

🤾 ГАНДБОЛ:

1️⃣ Сан Каэтано - Сорокаба
   Бразилия. Паулиста
   
   Счет: 9:6 (1Т, 17 мин)
   
   Рекомендация: П1 - коэф. 1.22
   
   📌 Анализ:
   - Ведут с разницей +3 в первом тайме
   - Уверенная игра хозяев
   - Хороший запас очков
   
   Источник: BetBoom live
   
   ✅ Категория: ОТЛИЧНЫЙ ⭐⭐⭐

---

📊 ИТОГО: 4 подходящих матча
   • Футбол: 1 (МЕРТВЫЙ)
   • Теннис: 2 (1 МЕРТВЫЙ + 1 ОТЛИЧНЫЙ)
   • Гандбол: 1 (ОТЛИЧНЫЙ)

---
⏰ Время анализа: 02:19-02:25 МСК
📈 Данные получены с BetBoom live
✅ ВСЕ МАТЧИ СООТВЕТСТВУЮТ КРИТЕРИЯМ СИСТЕМЫ

⚠️ ВАЖНО: Коэффициенты с замком 🔒 могут быть недоступны

🤖 TrueLiveBet | Честные прогнозы live-ставок
───────────────────────────────────"""

url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
payload = {
    'chat_id': CHANNEL,
    'text': message
}

try:
    response = requests.post(url, json=payload, timeout=10, verify=False)
    response.raise_for_status()
    print(f"OK: Message sent to {CHANNEL}")
    print(f"Status code: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"ERROR: {e}")

