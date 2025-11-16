#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система мониторинга и health checks для повышения надежности
"""

import json
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests
import urllib3
from zoneinfo import ZoneInfo

urllib3.disable_warnings()

TZ_MOSCOW = ZoneInfo("Europe/Moscow")
LOG_DIR = Path("logs")
HEALTH_LOG = LOG_DIR / "health_check.log"
STATUS_FILE = Path(".system_status.json")
ALERT_COOLDOWN = 300  # 5 минут между алертами

BOT_TOKEN = "7824400107:AAGZqPdS0E0N3HsYpD8TW9m8c-bapFd-RHk"
# Канал для критических алертов (отдельно от канала со ставками)
# Можно использовать: @username канала, chat_id (например, -1001234567890), или личный chat_id
# ВАЖНО: Укажи реальный канал или chat_id для алертов!
# Если None - алерты только логируются, но не отправляются в Telegram
ALERT_CHAT_ID = os.getenv("ALERTS_CHAT_ID", None)  # Укажи канал для алертов или установи переменную окружения


def _log(message: str) -> None:
    """Логирование в файл"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(TZ_MOSCOW).strftime("%Y-%m-%d %H:%M:%S")
    with HEALTH_LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")


def _send_alert(message: str) -> None:
    """Отправка критического алерта в Telegram (только в канал алертов, не в канал со ставками)"""
    if not ALERT_CHAT_ID:
        _log(f"Alert channel not configured. Alert message: {message[:100]}...")
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ALERT_CHAT_ID,
        "text": f"🚨 КРИТИЧЕСКОЕ УВЕДОМЛЕНИЕ СИСТЕМЫ\n\n{message}",
    }
    try:
        response = requests.post(url, json=payload, timeout=10, verify=False)
        if response.ok:
            _log(f"Alert sent to {ALERT_CHAT_ID}: {message[:50]}...")
        else:
            _log(f"Failed to send alert: {response.status_code}")
    except Exception as exc:
        _log(f"Error sending alert: {exc}")


def _should_send_alert(alert_type: str) -> bool:
    """Проверка cooldown для алертов"""
    if not STATUS_FILE.exists():
        return True
    
    try:
        data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        last_alert = data.get("last_alerts", {}).get(alert_type)
        if last_alert:
            last_time = datetime.fromisoformat(last_alert)
            # Если timezone-naive, добавляем timezone
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=TZ_MOSCOW)
            if (datetime.now(TZ_MOSCOW) - last_time).total_seconds() < ALERT_COOLDOWN:
                return False
        return True
    except Exception:
        return True


def _update_alert_time(alert_type: str) -> None:
    """Обновление времени последнего алерта"""
    data = {}
    if STATUS_FILE.exists():
        try:
            data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    
    if "last_alerts" not in data:
        data["last_alerts"] = {}
    
    data["last_alerts"][alert_type] = datetime.now(TZ_MOSCOW).isoformat()
    
    try:
        STATUS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def check_scheduler_status() -> Tuple[bool, str]:
    """Проверка статуса планировщика"""
    lock_file = Path(".auto_cycle.lock")
    if not lock_file.exists():
        return False, "Планировщик не запущен (нет lock файла)"
    
    try:
        pid = int(lock_file.read_text(encoding="utf-8").strip())
        # Проверяем, существует ли процесс (Windows)
        try:
            import psutil
            if not psutil.pid_exists(pid):
                return False, f"Процесс планировщика (PID {pid}) не существует"
            return True, f"Планировщик работает (PID {pid})"
        except ImportError:
            # Fallback: проверка через tasklist (Windows)
            import subprocess
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if str(pid) in result.stdout:
                return True, f"Планировщик работает (PID {pid})"
            return False, f"Процесс планировщика (PID {pid}) не существует"
    except (ValueError, Exception) as exc:
        return False, f"Ошибка проверки планировщика: {exc}"


def check_recent_activity() -> Tuple[bool, str]:
    """Проверка последней активности"""
    log_file = LOG_DIR / "auto_cycle.log"
    if not log_file.exists():
        return False, "Лог файл не найден"
    
    try:
        # Читаем последние строки
        with log_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return False, "Лог файл пуст"
            
            # Ищем последнюю запись с временем
            for line in reversed(lines[-50:]):
                if "[" in line and "]" in line:
                    try:
                        timestamp_str = line.split("]")[0].strip("[")
                        log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ_MOSCOW)
                        now = datetime.now(TZ_MOSCOW)
                        delta = (now - log_time).total_seconds()
                        
                        if delta > 3600:  # Больше часа
                            return False, f"Последняя активность {int(delta/60)} минут назад"
                        return True, f"Активность нормальная ({int(delta/60)} мин назад)"
                    except ValueError:
                        continue
        
        return False, "Не удалось найти временные метки в логе"
    except Exception as exc:
        return False, f"Ошибка чтения лога: {exc}"


def check_api_connectivity() -> Tuple[bool, str]:
    """Проверка доступности внешних API"""
    checks = []
    
    # Проверка Scores24 GraphQL
    try:
        response = requests.post(
            "https://scores24.live/graphql",
            json={"query": "query { __typename }"},
            timeout=5,
            verify=False
        )
        if response.ok:
            checks.append("Scores24: OK")
        else:
            checks.append(f"Scores24: {response.status_code}")
    except Exception as exc:
        checks.append(f"Scores24: Ошибка ({type(exc).__name__})")
    
    # Проверка Telegram API
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=5, verify=False)
        if response.ok:
            checks.append("Telegram: OK")
        else:
            checks.append(f"Telegram: {response.status_code}")
    except Exception as exc:
        checks.append(f"Telegram: Ошибка ({type(exc).__name__})")
    
    all_ok = all("OK" in check for check in checks)
    return all_ok, " | ".join(checks)


def check_disk_space() -> Tuple[bool, str]:
    """Проверка свободного места на диске"""
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_gb = free / (1024 ** 3)
        if free_gb < 1.0:
            return False, f"Критически мало места: {free_gb:.2f} GB"
        elif free_gb < 5.0:
            return True, f"Мало места: {free_gb:.2f} GB"
        return True, f"Места достаточно: {free_gb:.2f} GB"
    except Exception as exc:
        return True, f"Не удалось проверить: {exc}"


def run_health_check() -> Dict[str, Tuple[bool, str]]:
    """Запуск всех проверок"""
    results = {}
    
    _log("Запуск health check...")
    
    results["scheduler"] = check_scheduler_status()
    results["activity"] = check_recent_activity()
    results["api"] = check_api_connectivity()
    results["disk"] = check_disk_space()
    
    return results


def main():
    """Основная функция мониторинга"""
    results = run_health_check()
    
    critical_issues = []
    warnings = []
    
    for check_name, (is_ok, message) in results.items():
        if not is_ok:
            if check_name in ["scheduler", "activity"]:
                critical_issues.append(f"{check_name}: {message}")
            else:
                warnings.append(f"{check_name}: {message}")
        _log(f"{check_name}: {message}")
    
    # Отправка алертов
    if critical_issues:
        alert_msg = "Критические проблемы:\n" + "\n".join(f"• {issue}" for issue in critical_issues)
        if _should_send_alert("critical"):
            _send_alert(alert_msg)
            _update_alert_time("critical")
    
    if warnings:
        warning_msg = "Предупреждения:\n" + "\n".join(f"• {w}" for w in warnings)
        if _should_send_alert("warning"):
            _send_alert(warning_msg)
            _update_alert_time("warning")
    
    # Сохранение статуса
    status_data = {
        "last_check": datetime.now(TZ_MOSCOW).isoformat(),
        "results": {name: {"ok": ok, "message": msg} for name, (ok, msg) in results.items()},
        "critical_issues": len(critical_issues),
        "warnings": len(warnings),
    }
    
    try:
        STATUS_FILE.write_text(json.dumps(status_data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        _log(f"Ошибка сохранения статуса: {exc}")
    
    return 0 if not critical_issues else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        _log("Мониторинг остановлен пользователем")
        sys.exit(0)
    except Exception as exc:
        _log(f"Критическая ошибка мониторинга: {exc}")
        _send_alert(f"Мониторинг упал: {exc}")
        sys.exit(1)

