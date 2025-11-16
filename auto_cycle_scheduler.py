from __future__ import annotations

import argparse
import os
import random
import signal
import sys
import threading
import time
from datetime import datetime, time as time_cls
from pathlib import Path
from typing import List, Optional, Tuple

from zoneinfo import ZoneInfo

from send_live_report import main as run_live_cycle

TZ_MOSCOW = ZoneInfo("Europe/Moscow")

SCHEDULE_TIMES: List[Tuple[int, int]] = [
    (9, 0),
    (9, 20),
    (9, 40),
    (10, 0),
    (10, 20),
    (10, 40),
    (11, 0),
    (11, 20),
    (11, 40),
    (12, 0),
    (12, 20),
    (12, 40),
    (13, 0),
    (13, 20),
    (13, 40),
    (14, 0),
    (14, 20),
    (14, 40),
    (15, 0),
    (15, 20),
    (15, 40),
    (16, 0),
    (16, 20),
    (16, 40),
    (17, 0),
    (17, 20),
    (17, 40),
    (18, 0),
    (18, 20),
    (18, 40),
    (19, 0),
    (19, 20),
    (19, 40),
    (20, 0),
    (20, 20),
    (20, 40),
    (21, 0),
    (21, 20),
    (21, 40),
    (22, 0),
    (22, 20),
    (22, 40),
    (23, 0),
    (23, 20),
]

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "auto_cycle.log"
LOCK_FILE = Path(".auto_cycle.lock")
EMPTY_STREAK_FILE = Path(".auto_cycle_empty.txt")
CYCLE_TIMEOUT = 600  # 10 минут на выполнение анализа
MAX_CONSECUTIVE_ERRORS = 5

FALLBACK_DISCLAIMERS = [
    "⚠️ Все ставки несут риски. Играй ответственно.",
    "⚠️ Ставки — не гарантированный доход. Контролируйте банк.",
    "⚠️ Нет безрисковых ставок. Обдумывайте решения самостоятельно.",
]

IDLE_TIPS = [
    "💡 Напоминание: не рискуйте более 2% банка на одну ставку.",
    "✍️ Отмечай свои результаты: дата, матч, коэффициент и чем всё закончилось.",
    "📊 Поддерживай дисциплину банка: те же 2% на сигнал, без догонов.",
    "🔍 Наши сигналы — только по проверенной статистике. Ставим не сердцем, а цифрами.",
    "🗂️ Любая ставка — зафиксируй купон или скрин: потом легче считать реальный профит.",
    "⏱️ Без суеты. Всё успеем — сначала смотрим цифры, потом ставим.",
]


def _append_log(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(TZ_MOSCOW).strftime("%Y-%m-%d %H:%M:%S")
    LOG_FILE.open("a", encoding="utf-8").write(f"[{timestamp}] {message}\n")


def _make_slot_datetime(current_date: datetime.date, slot: Tuple[int, int]) -> datetime:
    hour, minute = slot
    return datetime.combine(
        current_date,
        time_cls(hour=hour, minute=minute),
        tzinfo=TZ_MOSCOW,
    )


def _acquire_lock() -> None:
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode("utf-8"))
        os.close(fd)
        _store_empty_streak(0)
    except FileExistsError:
        _append_log("Scheduler lock file exists; another instance is running. Exiting.")
        sys.exit(0)


def _release_lock() -> None:
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def _load_empty_streak() -> int:
    if not EMPTY_STREAK_FILE.exists():
        return 0
    try:
        return int(EMPTY_STREAK_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return 0


def _store_empty_streak(value: int) -> None:
    try:
        EMPTY_STREAK_FILE.write_text(str(value), encoding="utf-8")
    except Exception:
        pass




def _run_with_timeout(func, timeout_seconds: int, *args, **kwargs):
    """Запуск функции с таймаутом"""
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    if thread.is_alive():
        _append_log(f"WARNING: Cycle exceeded timeout ({timeout_seconds}s)")
        return None  # Таймаут
    
    if exception[0]:
        raise exception[0]
    
    return result[0]


def run_once(max_matches: int) -> Optional[int]:
    """Запуск одного цикла анализа с таймаутом"""
    now = datetime.now(TZ_MOSCOW)
    start_message = f"Launching live cycle (max_matches={max_matches}, timeout={CYCLE_TIMEOUT}s)"
    print(f"[{now:%Y-%m-%d %H:%M:%S}] {start_message}")
    _append_log(start_message)
    
    try:
        matches_found = _run_with_timeout(
            run_live_cycle,
            CYCLE_TIMEOUT,
            max_matches=max_matches
        )
        
        if matches_found is None:
            _append_log("ERROR: Cycle timed out")
            return None
        
        matches_found = matches_found or 0
        end = datetime.now(TZ_MOSCOW)
        duration = (end - now).total_seconds()
        finish_message = f"Cycle completed in {duration:.1f}s, matches: {matches_found}"
        print(f"[{end:%Y-%m-%d %H:%M:%S}] {finish_message}")
        _append_log(finish_message)
        return matches_found
        
    except Exception as exc:
        error_message = f"ERROR in cycle: {type(exc).__name__}: {exc}"
        print(f"[{datetime.now(TZ_MOSCOW):%Y-%m-%d %H:%M:%S}] {error_message}", file=sys.stderr)
        _append_log(error_message)
        return None


def run_scheduler(max_matches: int, grace_minutes: int, poll_interval: float) -> None:
    startup_message = (
        f"Scheduler started. Slots per day: {len(SCHEDULE_TIMES)}, grace={grace_minutes} min, "
        f"interval={poll_interval:.0f}s, timeout={CYCLE_TIMEOUT}s."
    )
    print(startup_message)
    _append_log(startup_message)
    executed_slots: set[Tuple[datetime.date, int, int]] = set()
    empty_streak = _load_empty_streak()
    consecutive_errors = 0

    def signal_handler(signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        _append_log("Received shutdown signal. Exiting gracefully...")
        _release_lock()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while True:
        try:
            now = datetime.now(TZ_MOSCOW)
            today = now.date()

            executed_slots = {slot for slot in executed_slots if slot[0] == today}

            for hour, minute in SCHEDULE_TIMES:
                slot_dt = _make_slot_datetime(today, (hour, minute))
                key = (today, hour, minute)

                if key in executed_slots:
                    continue

                delta = (now - slot_dt).total_seconds()
                if delta < 0:
                    continue

                if delta > grace_minutes * 60:
                    continue

                trigger_message = f"Triggering slot {hour:02d}:{minute:02d}"
                print(f"[{now:%Y-%m-%d %H:%M:%S}] {trigger_message}")
                _append_log(trigger_message)
                
                matches_found = run_once(max_matches=max_matches)
                
                if matches_found is None:
                    # Таймаут или ошибка
                    consecutive_errors += 1
                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        critical_msg = (
                            f"CRITICAL: {consecutive_errors} consecutive errors/timeouts. "
                            "Scheduler may need manual intervention."
                        )
                        _append_log(critical_msg)
                        # Можно отправить алерт
                        consecutive_errors = 0  # Сброс после алерта
                else:
                    consecutive_errors = 0  # Сброс при успехе
                    if matches_found:
                        empty_streak = 0
                    else:
                        empty_streak += 1
                    _store_empty_streak(empty_streak)
                
                executed_slots.add(key)

            time.sleep(poll_interval)
            
        except KeyboardInterrupt:
            _append_log("Scheduler interrupted by user")
            break
        except Exception as exc:
            consecutive_errors += 1
            error_message = f"CRITICAL ERROR in scheduler loop: {type(exc).__name__}: {exc}"
            print(f"[{datetime.now(TZ_MOSCOW):%Y-%m-%d %H:%M:%S}] {error_message}", file=sys.stderr)
            _append_log(error_message)
            
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                _append_log(f"Too many consecutive errors ({consecutive_errors}). Exiting.")
                break
            
            time.sleep(poll_interval)  # Небольшая пауза перед следующей итерацией


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scheduler for automatic live report cycles.")
    parser.add_argument("--once", action="store_true", help="Run single cycle immediately and exit.")
    parser.add_argument("--max-matches", type=int, default=5, help="How many matches to include per cycle.")
    parser.add_argument(
        "--grace-minutes",
        type=int,
        default=7,
        help="How many minutes after the scheduled slot we still try to run it.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=20.0,
        help="Scheduler loop sleep interval in seconds.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    _acquire_lock()
    args = parse_args()
    try:
        if args.once:
            run_once(max_matches=args.max_matches)
        else:
            run_scheduler(
                max_matches=args.max_matches,
                grace_minutes=args.grace_minutes,
                poll_interval=args.poll_interval,
            )
    finally:
        _release_lock()

