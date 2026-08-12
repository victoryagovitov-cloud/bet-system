from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import httpx
from loguru import logger

ROOT = Path(__file__).resolve().parents[1]
MAX_API_BASE = "https://platform-api2.max.ru"


def _send_max_http(text: str, chat_id: int | str, token: str) -> str:
    """Отправка через официальный Bot API (platform-api2.max.ru)."""
    url = f"{MAX_API_BASE}/messages"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    # chat_id как query — так уже успешно отправляли тест в канал
    params = {"chat_id": int(chat_id)}
    payload = {"text": text}
    with httpx.Client(timeout=30.0, verify=False) as client:
        resp = client.post(url, headers=headers, params=params, json=payload)
        resp.raise_for_status()
        data = resp.json()
    mid = ((data.get("message") or {}).get("body") or {}).get("mid")
    return mid or f"max:{chat_id}"


def publish_signal(
    text: str,
    *,
    chat_id: str,
    token: str,
    publish_mode: str = "dry_run",
    match_id: int | None = None,
) -> str:
    """
    Публикация в MAX или dry-run в файл.
    Возвращает идентификатор публикации (message id / filepath).
    """
    mode = (publish_mode or "dry_run").lower()
    if mode != "live":
        out_dir = ROOT / "data" / "signals_dry_run"
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        suffix = f"_{match_id}" if match_id else ""
        path = out_dir / f"signal_{ts}{suffix}.txt"
        path.write_text(text, encoding="utf-8")
        logger.info("dry-run signal saved: {}", path)
        return str(path)

    if not token or not chat_id:
        raise ValueError("MAX_BOT_TOKEN / MAX_CHANNEL_CHAT_ID не заданы для live-публикации")

    ref = _send_max_http(text, chat_id, token)
    logger.info("signal published to MAX chat_id={} ref={}", chat_id, ref)
    return str(ref)
