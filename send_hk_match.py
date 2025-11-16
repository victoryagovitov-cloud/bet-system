# -*- coding: utf-8 -*-
"""
Отправка сообщения по матчу Гонконг ФК - Истерн СК
"""
import json
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter, Retry
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def send():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    token = config["notifications"]["telegram"]["bot_token"]
    chat_id = config["notifications"]["telegram"]["channel_username"]

    now = datetime.now()
    message = (
        f"🎯 LIVE-АНАЛИЗ • {now:%H:%M} МСК, {now:%d.%m.%Y}\n\n"
        "—————————————\n\n"
        "⚽ ФУТБОЛ ⚽\n\n"
        "—————————————\n\n"
        "1️⃣ Гонконг ФК - Истерн СК\n"
        "   Гонконг. Премьер-лига\n"
        "   Счет: 0:1 (перерыв)\n"
        "   Рекомендация: П2 - коэф. ~1.11\n\n"
        "   📌 Истерн ведёт 1:0, удары 4:1 и 3:1 в створ — фаворит контролирует матч.\n"
        "   ✅ ИДЕАЛЬНЫЙ ⭐⭐⭐⭐\n\n"
        "—————————————\n\n"
        "🔥 @TrueLiveBet | Честные прогнозы с ИИ\n\n"
        "⚠️ Ставки — это риск. Играйте ответственно и в рамках своих возможностей."
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    resp = session.post(url, data=data, timeout=60, verify=False)
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    print(send())

