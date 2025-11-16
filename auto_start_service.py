#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматический запуск всех компонентов системы при старте
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

TZ_MOSCOW = ZoneInfo("Europe/Moscow")
LOG_DIR = Path("logs")
STARTUP_LOG = LOG_DIR / "startup.log"
LOCK_FILE = Path(".auto_start.lock")

COMPONENTS = {
    "watchdog": {
        "script": "watchdog_service.py",
        "lock": ".watchdog.lock",
        "delay": 2,
    },
    "scheduler": {
        "script": "auto_cycle_scheduler.py",
        "lock": ".auto_cycle.lock",
        "delay": 3,  # Задержка между попытками проверки
    },
}


def _log(message: str) -> None:
    """Логирование запуска"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(TZ_MOSCOW).strftime("%Y-%m-%d %H:%M:%S")
    with STARTUP_LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")


def _is_running(lock_file: Path) -> bool:
    """Проверка, запущен ли компонент"""
    if not lock_file.exists():
        return False
    
    try:
        pid = int(lock_file.read_text(encoding="utf-8").strip())
        # Проверка процесса (Windows)
        is_alive = False
        try:
            import psutil
            is_alive = psutil.pid_exists(pid)
        except ImportError:
            # Fallback через tasklist
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_alive = str(pid) in result.stdout
        
        # Если процесс не существует, удаляем старый lock файл
        if not is_alive:
            try:
                lock_file.unlink(missing_ok=True)
                _log(f"Удален старый lock файл (процесс {pid} не существует)")
            except Exception:
                pass
        
        return is_alive
    except Exception:
        # Если не удалось прочитать lock файл, удаляем его
        try:
            lock_file.unlink(missing_ok=True)
        except Exception:
            pass
        return False


def _start_component(name: str, config: dict) -> bool:
    """Запуск компонента"""
    script = config["script"]
    lock_file = Path(config["lock"])
    
    # Проверяем, не запущен ли уже
    if _is_running(lock_file):
        _log(f"{name}: уже запущен (PID из {lock_file})")
        return True
    
    try:
        _log(f"Запуск {name} ({script})...")
        # Запуск в фоне без окна (Windows)
        process = subprocess.Popen(
            [sys.executable, script],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Ждем немного для инициализации с повторными проверками
        max_attempts = 3
        for attempt in range(max_attempts):
            time.sleep(config["delay"])
            if _is_running(lock_file):
                _log(f"{name}: успешно запущен (PID {process.pid})")
                return True
            if attempt < max_attempts - 1:
                _log(f"{name}: ожидание lock файла (попытка {attempt + 1}/{max_attempts})...")
        
        # Финальная проверка
        if _is_running(lock_file):
            _log(f"{name}: успешно запущен (PID {process.pid})")
            return True
        else:
            _log(f"{name}: запущен, но lock файл не появился. Возможно, ошибка.")
            return False
            
    except Exception as exc:
        _log(f"{name}: ошибка запуска - {exc}")
        return False


def main():
    """Основная функция автозапуска"""
    # Проверка блокировки
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text(encoding="utf-8").strip())
            if _is_running(LOCK_FILE):
                _log("Автозапуск уже работает. Выход.")
                return 0
        except Exception:
            pass
    
    # Создаем lock файл
    try:
        LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    except Exception as exc:
        _log(f"Ошибка создания lock файла: {exc}")
        return 1
    
    _log("=" * 60)
    _log("Автоматический запуск системы")
    _log("=" * 60)
    
    results = {}
    
    # Запускаем компоненты по порядку
    for name, config in COMPONENTS.items():
        results[name] = _start_component(name, config)
        time.sleep(1)  # Небольшая пауза между запусками
    
    # Итоги
    _log("=" * 60)
    _log("Итоги запуска:")
    for name, success in results.items():
        status = "[OK]" if success else "[FAIL]"
        _log(f"  {status} {name}: {'OK' if success else 'FAILED'}")
    _log("=" * 60)
    
    # Удаляем lock файл после завершения
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass
    
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        _log("Автозапуск прерван пользователем")
        sys.exit(0)
    except Exception as exc:
        _log(f"Критическая ошибка автозапуска: {exc}")
        sys.exit(1)

