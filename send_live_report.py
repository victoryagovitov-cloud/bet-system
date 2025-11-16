#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import os
import requests
import urllib3
from zoneinfo import ZoneInfo

from generate_live_report import (
    generate_live_report,
    _get_recent_slugs,
    _filter_duplicates,
)
from recommendation_logger import log_recommendations

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from tuning_settings import SETTINGS as TUNING_SETTINGS
except ImportError:

    @dataclass(frozen=True)
    class _DefaultSettings:
        max_matches: int = 5
        filter_relaxation: float = 1.0
        enable_secondary_dedup: bool = True

    TUNING_SETTINGS = _DefaultSettings()

BOT_TOKEN = os.getenv("TLB_TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TLB_TELEGRAM_CHAT_ID", "@TrueLiveBet")


def send_report(
    message: str,
    timeout: int = 30,
    retries: int = 10,  # Увеличено с 5 до 10 попыток
    base_delay: float = 2.0,  # Уменьшена базовая задержка с 3.0 до 2.0
    backoff_factor: float = 1.5,  # Уменьшен фактор роста с 1.8 до 1.5
) -> Optional[requests.Response]:
    """Отправка сообщения в Telegram с агрессивными повторными попытками"""
    if not BOT_TOKEN:
        print("ERROR: Missing env var TLB_TELEGRAM_BOT_TOKEN. Telegram send disabled.")
        return None
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, json=payload, timeout=timeout, verify=False)
            print(f"Attempt {attempt}/{retries}: HTTP {response.status_code}")
            
            if response.ok:
                print(f"SUCCESS: Message sent successfully on attempt {attempt}")
                return response
            else:
                # HTTP ошибка (не 200), но соединение установлено
                error_text = response.text[:200]  # Первые 200 символов для лога
                print(f"Attempt {attempt}: HTTP error {response.status_code}: {error_text}")
                last_error = f"HTTP {response.status_code}: {error_text}"
                
        except requests.exceptions.Timeout as exc:
            print(f"Attempt {attempt}/{retries}: Timeout after {timeout}s")
            last_error = f"Timeout: {exc}"
        except requests.exceptions.ConnectionError as exc:
            print(f"Attempt {attempt}/{retries}: ConnectionError: {exc}")
            last_error = f"ConnectionError: {exc}"
        except requests.exceptions.RequestException as exc:
            print(f"Attempt {attempt}/{retries}: RequestException: {exc}")
            last_error = f"RequestException: {exc}"
        except Exception as exc:
            print(f"Attempt {attempt}/{retries}: Unexpected error {type(exc).__name__}: {exc}")
            last_error = f"Unexpected: {type(exc).__name__}: {exc}"

        if attempt < retries:
            # Увеличиваем задержку постепенно, но не слишком агрессивно
            delay = base_delay * (backoff_factor ** (attempt - 1))
            # Максимальная задержка - 15 секунд
            delay = min(delay, 15.0)
            print(f"Retrying in {int(round(delay))} seconds...")
            time.sleep(delay)
        else:
            # Последняя попытка не удалась - начинаем принудительную отправку
            print(f"WARNING: All {retries} regular attempts exhausted. Last error: {last_error}")
            print("Starting FORCED delivery attempts with extended timeout...")
            
            # Принудительные попытки с увеличенным timeout и более длинными задержками
            forced_retries = 5
            forced_timeout = 60  # Увеличенный timeout для принудительных попыток
            forced_base_delay = 10.0  # Базовая задержка 10 секунд
            
            for forced_attempt in range(1, forced_retries + 1):
                try:
                    print(f"FORCED attempt {forced_attempt}/{forced_retries} (timeout={forced_timeout}s)...")
                    response = requests.post(
                        url, 
                        json=payload, 
                        timeout=forced_timeout, 
                        verify=False
                    )
                    
                    if response.ok:
                        print(f"SUCCESS: Message sent successfully on FORCED attempt {forced_attempt}")
                        return response
                    else:
                        error_text = response.text[:200]
                        print(f"FORCED attempt {forced_attempt}: HTTP {response.status_code}: {error_text}")
                        last_error = f"HTTP {response.status_code}: {error_text}"
                        
                except requests.exceptions.Timeout as exc:
                    print(f"FORCED attempt {forced_attempt}: Timeout after {forced_timeout}s")
                    last_error = f"Timeout: {exc}"
                except requests.exceptions.ConnectionError as exc:
                    print(f"FORCED attempt {forced_attempt}: ConnectionError: {exc}")
                    last_error = f"ConnectionError: {exc}"
                except Exception as exc:
                    print(f"FORCED attempt {forced_attempt}: Error {type(exc).__name__}: {exc}")
                    last_error = f"{type(exc).__name__}: {exc}"
                
                if forced_attempt < forced_retries:
                    # Увеличиваем задержку для принудительных попыток
                    forced_delay = forced_base_delay * (1.5 ** (forced_attempt - 1))
                    forced_delay = min(forced_delay, 30.0)  # Максимум 30 секунд
                    print(f"Waiting {int(round(forced_delay))} seconds before next FORCED attempt...")
                    time.sleep(forced_delay)
            
            # Все принудительные попытки тоже не удались
            print(f"CRITICAL: All {retries} regular + {forced_retries} forced attempts failed.")
            print(f"Final error: {last_error}")
            return None

    return None


def _split_sections_into_messages(sections: List[str], max_chars: Optional[int] = None) -> List[str]:
    if max_chars is None:
        # Берём из настроек, по умолчанию 2800
        max_chars = getattr(TUNING_SETTINGS, "telegram_chunk_max_chars", 2800)
    if not sections:
        return []
    header = sections[0]
    body = sections[1:]
    messages: List[str] = []
    suffix = 1

    def _make_header(suffix_index: int) -> str:
        return header if suffix_index == 1 else f"{header} (продолжение {suffix_index})"

    current_sections = [_make_header(suffix)]
    current_len = len(current_sections[0])

    for section in body:
        section_len = len(section)
        # Если секция сама очень длинная, отправляем текущий блок и начинаем новый
        if (
            current_len > 0
            and current_len + 2 + section_len > max_chars
            and len(current_sections) > 1
        ):
            messages.append("\n\n".join(current_sections))
            suffix += 1
            current_sections = [_make_header(suffix)]
            current_len = len(current_sections[0])

        # Если даже одной секции достаточно для превышения лимита – отправляем как есть
        if current_len + 2 + section_len > max_chars and len(current_sections) == 1:
            # Сначала отправляем заголовок
            messages.append("\n\n".join(current_sections))
            suffix += 1
            current_sections = [_make_header(suffix)]
            current_len = len(current_sections[0])

        current_sections.append(section)
        current_len += 2 + section_len

    if current_sections:
        messages.append("\n\n".join(current_sections))

    return messages


def main(max_matches: Optional[int] = None):
    if max_matches is None:
        max_matches = TUNING_SETTINGS.max_matches

    message, matches, context = generate_live_report(max_matches=max_matches)
    generated_at = context.get("generated_at")
    if generated_at is None:
        generated_at = datetime.now(ZoneInfo("Europe/Moscow"))
        context["generated_at"] = generated_at

    # Дополнительная проверка дедупликации перед отправкой делаем только если включено в настройках
    if TUNING_SETTINGS.enable_secondary_dedup:
        recent_slugs = _get_recent_slugs(hours=4)
        matches_before_final_check = len(matches)
        matches = _filter_duplicates(matches, recent_slugs)
        if len(matches) < matches_before_final_check:
            print(f"WARNING: Final deduplication check filtered {matches_before_final_check - len(matches)} additional duplicates!")
            # Обновляем сообщение, если матчи были отфильтрованы
            if not matches:
                message = "В данный момент подходящих матчей для рекомендации не найдено. Следующий анализ через 45 минут."
            else:
                # Перегенерируем сообщение с отфильтрованными матчами
                message, _, _ = generate_live_report(max_matches=len(matches))
                # Но это может привести к бесконечному циклу, поэтому просто предупреждаем
                print(f"WARNING: Message contains {len(matches)} matches after final deduplication check")
    else:
        print("DEBUG: Final deduplication check disabled in tuning_settings.")

    print(message)

    sections = context.get("sections") if context else None
    messages_to_send = []
    if sections:
        messages_to_send = _split_sections_into_messages(sections)
    if not messages_to_send:
        messages_to_send = [message]

    responses: List[requests.Response] = []
    pause_between = float(getattr(TUNING_SETTINGS, "telegram_chunk_pause_seconds", 2.0))

    for idx, chunk in enumerate(messages_to_send, 1):
        print(f"Sending chunk {idx}/{len(messages_to_send)} (len={len(chunk)} characters)")
        response = send_report(chunk)
        if response is None:
            print(f"Failed to send chunk {idx}/{len(messages_to_send)}. Aborting.")
            break
        responses.append(response)
        if idx < len(messages_to_send) and pause_between > 0:
            time.sleep(pause_between)

    message_id: Optional[int] = None
    if len(responses) != len(messages_to_send):
        print("Failed to send report after retries.")
        # НЕ записываем в лог, если отправка не удалась - матчи можно будет отправить снова
    else:
        if responses:
            try:
                payload = responses[-1].json()
                message_id = payload.get("result", {}).get("message_id")
            except ValueError:
                print("Warning: unable to parse Telegram response JSON.")
        
        # Записываем в лог ТОЛЬКО если все части были успешно отправлены
        log_recommendations(matches, generated_at, message_id)

    return len(matches)


if __name__ == "__main__":
    main()
