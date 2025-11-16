# -*- coding: utf-8 -*-
"""
Разовая отправка текущего сообщения в канал Telegram
"""
import json
import time
from datetime import datetime

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def send():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    bot_token = config["notifications"]["telegram"]["bot_token"]
    channel_username = config["notifications"]["telegram"]["channel_username"]

    current_time = datetime.now().strftime("%H:%M")
    current_date = datetime.now().strftime("%d.%m.%Y")

    message = f"""🎯 LIVE-АНАЛИЗ • {current_time} МСК, {current_date}

—————————————

⚽ ФУТБОЛ ⚽

—————————————

1️⃣ Гонконг ФК - Истерн СК
   Гонконг. Премьер-лига
   Счет: 0:1 (перерыв)
   Рекомендация: П2 - коэф. ~1.11

   📌 Истерн ведёт 1:0, удары 4:1 и 3:1 в створ — фаворит контролирует ход матча.
   ✅ ИДЕАЛЬНЫЙ ⭐⭐⭐⭐

—————————————

🔥 @TrueLiveBet | Честные прогнозы с ИИ

⚠️ Ставки — это риск. Играйте ответственно и в рамках своих возможностей."""

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": channel_username, "text": message}

    for attempt in range(2):
        try:
            resp = requests.get(url, params=data, verify=False, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            if result.get("ok"):
                return result
            raise RuntimeError(result)
        except Exception as exc:
            print(f"Attempt {attempt + 1} failed: {exc}")
            if attempt == 0:
                time.sleep(3)
            else:
                raise


if __name__ == "__main__":
    res = send()
    print("Sent:", res.get("ok"))

