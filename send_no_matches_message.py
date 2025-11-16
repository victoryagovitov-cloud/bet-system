# -*- coding: utf-8 -*-
import os
import time
import json
import requests
from datetime import datetime
from pathlib import Path

DISCLAIMER_FILE = Path('ДИСКЛЕЙМЕРЫ_ДЛЯ_СООБЩЕНИЙ.txt')
DISCLAIMER_STATE_FILE = Path('.disclaimer_state.json')

def load_disclaimers():
    if not DISCLAIMER_FILE.exists():
        return []
    disclaimers = []
    buffer = []
    import re
    with DISCLAIMER_FILE.open('r', encoding='utf-8') as f:
        for raw_line in f:
            text = raw_line.strip()
            if not text:
                if buffer:
                    combined = ' '.join(buffer)
                    if re.match(r'^\d+\.\s', buffer[0]):
                        combined = re.sub(r'^\d+\.\s*', '', combined)
                        disclaimers.append(combined)
                    buffer = []
                continue
            if not buffer and not re.match(r'^\d+\.\s', text):
                continue
            buffer.append(text)
    if buffer:
        combined = ' '.join(buffer)
        import re as _re
        if _re.match(r'^\d+\.\s', buffer[0]):
            combined = _re.sub(r'^\d+\.\s*', '', combined)
            disclaimers.append(combined)
    return disclaimers

def get_next_disclaimer():
    disclaimers = load_disclaimers()
    if not disclaimers:
        return "⚠️ Ставки — это риск. Играйте ответственно и в рамках своих возможностей."

    index = 0
    try:
        if DISCLAIMER_STATE_FILE.exists():
            with DISCLAIMER_STATE_FILE.open('r', encoding='utf-8') as f:
                state = json.load(f)
                index = (state.get('index', -1) + 1) % len(disclaimers)
        else:
            index = 0
    except Exception:
        index = 0

    try:
        DISCLAIMER_STATE_FILE.write_text(json.dumps({'index': index}, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass

    return disclaimers[index]

def send_no_matches_message():
    """Отправляет сообщение о том, что подходящих матчей не найдено"""

    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    current_time = datetime.now().strftime('%H:%M')
    current_date = datetime.now().strftime('%d.%m.%Y')
    disclaimer = get_next_disclaimer()

    message = f"""🎯 LIVE-АНАЛИЗ • {current_time} МСК, {current_date}

—————————————

⚽ ФУТБОЛ ⚽

—————————————

В данный момент подходящих матчей для рекомендации не найдено.

Следующий анализ через 45 минут.

—————————————

🔥 @TrueLiveBet | Честные прогнозы с ИИ

{disclaimer}"""

    url = f"https://api.telegram.org/bot{config['notifications']['telegram']['bot_token']}/sendMessage"
    payload = {
        'chat_id': config['notifications']['telegram']['channel_username'],
        'text': message
    }

    os.environ.pop("REQUESTS_CA_BUNDLE", None)
    os.environ.pop("CURL_CA_BUNDLE", None)

    session = requests.Session()
    session.verify = False
    session.headers.update({
        "Connection": "close",
        "User-Agent": "TrueLiveBet-Autobot/1.0"
    })

    for attempt in range(1, 6):
        try:
            response = session.post(url, json=payload, timeout=30)
            if response.ok:
                print(f"Сообщение отправлено (попытка {attempt}) в @TrueLiveBet")
                print(f"Время: {current_time} МСК, {current_date}")
                return True
            print(f"Ошибка Telegram (попытка {attempt}): {response.text}")
        except Exception as exc:
            print(f"Ошибка соединения (попытка {attempt}): {exc}")
        pause = min(3 * attempt, 10)
        time.sleep(pause)

    print("Telegram не принял сообщение после 5 попыток")
    return False

if __name__ == "__main__":
    send_no_matches_message()
