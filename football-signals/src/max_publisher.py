from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

ROOT = Path(__file__).resolve().parents[1]


async def _send_max(text: str, chat_id: int | str, token: str) -> None:
    try:
        from maxapi import Bot  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Пакет maxapi не установлен. Добавьте maxapi в requirements и pip install, "
            "либо оставьте PUBLISH_MODE=dry_run."
        ) from exc

    bot = Bot(token)
    await bot.send_message(chat_id=int(chat_id), text=text, format="markdown")


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

    asyncio.run(_send_max(text, chat_id, token))
    logger.info("signal published to MAX chat_id={}", chat_id)
    return f"max:{chat_id}"
