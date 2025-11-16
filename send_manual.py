import json
import os
import time

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def send_message():
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    with open("current_live_analysis_mcp.txt", "r", encoding="utf-8") as f:
        text = f.read()

    url = (
        "https://api.telegram.org/bot"
        + cfg["notifications"]["telegram"]["bot_token"]
        + "/sendMessage"
    )

    payload = {
        "chat_id": cfg["notifications"]["telegram"]["channel_username"],
        "text": text,
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
            resp = session.post(url, json=payload, timeout=30)
            if resp.ok:
                print("Telegram response:", resp.text)
                return True
            print(f"Attempt {attempt} failed:", resp.text)
        except Exception as exc:
            print(f"Attempt {attempt} failed:", exc)
        time.sleep(min(3 * attempt, 10))

    return False


if __name__ == "__main__":
    if not send_message():
        raise SystemExit("Failed to send Telegram message")

