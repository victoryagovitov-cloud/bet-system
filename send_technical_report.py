import requests
import json
from datetime import datetime
import urllib3

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def send_to_telegram():
    """Отправка технического отчета в Telegram канал"""
    
    # Читаем конфиг
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    bot_token = config['notifications']['telegram']['bot_token']
    channel = config['notifications']['telegram']['channel_username']
    
    # Формируем сообщение
    current_time = datetime.now().strftime('%H:%M')
    current_date = datetime.now().strftime('%d.%m.%Y')
    
    message = f"""───────────────────────────────────
📊 АНАЛИЗ LIVE-МАТЧЕЙ НА {current_time} МСК ({current_date})

⚠️ ТЕХНИЧЕСКИЙ ОТЧЕТ ⚠️

🔍 НАЙДЕНО ПОТЕНЦИАЛЬНЫХ МАТЧЕЙ:

⚽ ФУТБОЛ (1 матч):
Шапекоэнсе - Операрио ПР
Бразилия. Серия B
Счет: 2:0 (2Т, 49 мин)
Коэфф П1: 1.06

🎾 ТЕННИС (2 матча - МЕРТВЫЕ):
1) Захрай П. - Квятковски Т.
ATP Challenger. Шарлоттсвилл
Счет: 1:3 в сетах, 40:A во 2-м
Коэфф П2: 1.01 (ЗАМОК 🔒)

2) Парный разряд (жен)
WTA 125. Кали
Счет: 1:0, 5:2 во 2-м
Коэфф П1: 1.01 (ЗАМОК 🔒)

🤾 ГАНДБОЛ (1 матч):
Сан Каэтано - Сорокаба
Бразилия. Паулиста
Счет: 4:1 (1Т, 8 мин)
Коэфф П1: 1.19

---

❌ ПРОБЛЕМА С ПРОВЕРКОЙ СТАТИСТИКИ:

• Flashscore.ru не отвечает (таймаут)
• Web search не дает реальных данных
• НЕ ПРОВЕРЕНЫ позиции в таблицах
• НЕ ПРОВЕРЕНЫ рейтинги ATP/WTA
• НЕ ПРОВЕРЕНА статистика команд

---

🔴 РЕКОМЕНДАЦИИ: НЕТ

Согласно правилам системы: "БЕЗ ПРОВЕРКИ СТАТИСТИКИ ЧЕРЕЗ НЕСКОЛЬКО ИСТОЧНИКОВ - НЕ ОТПРАВЛЯТЬ!"

Матчи НЕ рекомендуются для ставок из-за отсутствия подтверждения статистики.

---

📊 ИТОГО:
• Найдено матчей: 4
• Рекомендовано: 0
• Причина: технические проблемы с источниками

---
⏰ Время анализа: 02:09-02:15 МСК
⚠️ Следующий анализ после восстановления доступа к источникам статистики

🤖 TrueLiveBet | Честные прогнозы live-ставок
───────────────────────────────────"""
    
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    
    payload = {
        'chat_id': channel,
        'text': message
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10, verify=False)
        response.raise_for_status()
        print(f"OK: Message sent to {channel}")
        print(f"Status code: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Server response: {e.response.text}")
        return False

if __name__ == "__main__":
    send_to_telegram()

