#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Watchdog сервис для автоматического перезапуска планировщика
"""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ_MOSCOW = ZoneInfo("Europe/Moscow")
LOG_DIR = Path("logs")
WATCHDOG_LOG = LOG_DIR / "watchdog.log"
LOCK_FILE = Path(".watchdog.lock")
SCHEDULER_SCRIPT = "auto_cycle_scheduler.py"
MAX_RESTART_ATTEMPTS = 3
RESTART_COOLDOWN = 300  # 5 минут между перезапусками


def _log(message: str) -> None:
    """Логирование"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(TZ_MOSCOW).strftime("%Y-%m-%d %H:%M:%S")
    with WATCHDOG_LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")


def _acquire_lock() -> bool:
    """Получение блокировки watchdog"""
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode("utf-8"))
        os.close(fd)
        return True
    except FileExistsError:
        return False


def _release_lock() -> None:
    """Освобождение блокировки"""
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def _is_scheduler_running() -> bool:
    """Проверка, запущен ли планировщик"""
    scheduler_lock = Path(".auto_cycle.lock")
    if not scheduler_lock.exists():
        return False
    
    try:
        pid = int(scheduler_lock.read_text(encoding="utf-8").strip())
        # Проверка существования процесса (Windows)
        try:
            import psutil
            return psutil.pid_exists(pid)
        except ImportError:
            # Fallback: проверка через tasklist (Windows)
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return str(pid) in result.stdout
    except Exception:
        return False


def _start_scheduler() -> bool:
    """Запуск планировщика"""
    try:
        _log("Запуск планировщика...")
        # Запуск в фоне (Windows)
        subprocess.Popen(
            [sys.executable, SCHEDULER_SCRIPT],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)  # Даем время на запуск
        return _is_scheduler_running()
    except Exception as exc:
        _log(f"Ошибка запуска планировщика: {exc}")
        return False


def main():
    """Основной цикл watchdog"""
    if not _acquire_lock():
        print("Watchdog уже запущен. Выход.")
        sys.exit(0)
    
    _log("Watchdog сервис запущен")
    
    restart_count = 0
    last_restart_time = 0
    
    try:
        while True:
            if not _is_scheduler_running():
                now = time.time()
                
                # Проверка cooldown
                if now - last_restart_time < RESTART_COOLDOWN:
                    _log(f"Планировщик не работает, но cooldown активен. Ожидание...")
                elif restart_count >= MAX_RESTART_ATTEMPTS:
                    _log(f"Достигнут лимит перезапусков ({MAX_RESTART_ATTEMPTS}). Требуется ручное вмешательство.")
                    # Можно отправить алерт
                    break
                else:
                    _log(f"Планировщик не работает. Попытка перезапуска {restart_count + 1}/{MAX_RESTART_ATTEMPTS}")
                    if _start_scheduler():
                        _log("Планировщик успешно перезапущен")
                        restart_count = 0
                    else:
                        restart_count += 1
                        _log(f"Не удалось перезапустить планировщик. Попыток: {restart_count}/{MAX_RESTART_ATTEMPTS}")
                    last_restart_time = now
            else:
                # Планировщик работает, сбрасываем счетчик
                if restart_count > 0:
                    _log("Планировщик восстановлен. Сброс счетчика перезапусков.")
                    restart_count = 0
            
            time.sleep(60)  # Проверка каждую минуту
            
    except KeyboardInterrupt:
        _log("Watchdog остановлен пользователем")
    except Exception as exc:
        _log(f"Критическая ошибка watchdog: {exc}")
    finally:
        _release_lock()


if __name__ == "__main__":
    main()

