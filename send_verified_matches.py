# -*- coding: utf-8 -*-
"""
Отправка только проверенных на Scores24 матчей
"""
import os
import json
import time
import requests
import urllib3
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MESSAGE_PATH = Path('current_live_analysis_mcp.txt')


def send_verified_matches(message_override: str | None = None) -> bool:
    """
    Отправляет готовое сообщение в Telegram-канал.
    По умолчанию читает текст из current_live_analysis_mcp.txt,
    чтобы весь шаблон заполнялся в одном месте (анализатором).

    Args:
        message_override: необязательный текст сообщения. Если передан,
                          используется он; иначе читаем файл.
    """
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("ERROR: Файл config.json не найден.")
        return False

    bot_token = config['notifications']['telegram']['bot_token']
    channel_username = config['notifications']['telegram']['channel_username']
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    if message_override is not None:
        message_text = message_override
    else:
        if not MESSAGE_PATH.exists():
            print("ERROR: current_live_analysis_mcp.txt отсутствует, нечего отправлять.")
            return False
        message_text = MESSAGE_PATH.read_text(encoding='utf-8').strip()
        if not message_text:
            print("ERROR: current_live_analysis_mcp.txt пустой.")
            return False

    payload = {
        'chat_id': channel_username,
        'text': message_text
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
                result = response.json()
                print("SUCCESS: Сообщение с проверенными матчами отправлено в канал @TrueLiveBet")
                print(f"Telegram ID: {result.get('result', {}).get('message_id')}")
                return True

            print(f"ERROR: Telegram ответ (попытка {attempt}): {response.text}")
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
        time.sleep(min(3 * attempt, 10))

    print("ERROR: Не удалось отправить сообщение после 5 попыток")
    return False

if __name__ == "__main__":
    send_verified_matches()
