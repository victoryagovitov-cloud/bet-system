#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для подготовки проекта к работе с GitHub.
Определяет основные файлы для коммита.
"""

from pathlib import Path

# Основные файлы системы
CORE_FILES = [
    # Основные модули
    "generate_live_report.py",
    "graphql_live_analyzer.py",
    "graphql_tennis_analyzer.py",
    "graphql_handball_analyzer.py",
    "scores24_graphql_client.py",
    "scores24_snapshot_enricher.py",
    
    # Отправка и планировщик
    "send_live_report.py",
    "auto_cycle_scheduler.py",
    "recommendation_logger.py",
    
    # Конфигурация
    "config.json",
    "requirements.txt",
    
    # Документация
    "ПОЛНЫЙ_АЛГОРИТМ_РАБОТЫ.md",
    "README.md",
    ".gitignore",
]

# Вспомогательные файлы (опционально)
HELPER_FILES = [
    "telegram_simple.py",
    "start_scheduler.bat",
]

# Файлы для исключения (тестовые, временные)
EXCLUDE_PATTERNS = [
    "test_*.py",
    "debug_*.py",
    "check_*.py",
    "*_test.py",
    "*.log",
    "*.html",
    "*.json",
    "*.txt",
    "*.bat",
    "*.ahk",
]

def check_files():
    """Проверяет наличие основных файлов."""
    missing = []
    for file in CORE_FILES:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print("[WARNING] Отсутствуют файлы:")
        for f in missing:
            print(f"  - {f}")
    else:
        print("[OK] Все основные файлы на месте")
    
    return len(missing) == 0

if __name__ == "__main__":
    print("Проверка готовности к GitHub...")
    print("=" * 60)
    check_files()
    print(f"\nОсновных файлов для коммита: {len(CORE_FILES)}")

