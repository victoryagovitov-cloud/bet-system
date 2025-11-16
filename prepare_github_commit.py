#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для подготовки файлов к коммиту в GitHub
Определяет основные файлы системы и исключает тестовые/временные
"""

from pathlib import Path

# Основные файлы системы (обязательно)
CORE_FILES = [
    "generate_live_report.py",
    "graphql_live_analyzer.py",
    "graphql_tennis_analyzer.py",
    "graphql_handball_analyzer.py",
    "scores24_graphql_client.py",
    "scores24_snapshot_enricher.py",
    "send_live_report.py",
    "auto_cycle_scheduler.py",
    "recommendation_logger.py",
    "telegram_simple.py",
    "requirements.txt",
    "config.json",
    "ПОЛНЫЙ_АЛГОРИТМ_РАБОТЫ.md",
    ".gitignore",
    "README.md",
]

# Документация (важно, но не критично)
DOC_FILES = [
    "*.md",
]

# Исключить (тестовые, временные)
EXCLUDE_PATTERNS = [
    "test_*.py",
    "debug_*.py",
    "check_*.py",
    "*.html",
    "*.json",
    "*.txt",
    "*.bat",
    "*.ahk",
]

def check_files():
    """Проверяет наличие основных файлов"""
    missing = []
    for file in CORE_FILES:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print("[WARNING] Отсутствуют критические файлы:")
        for f in missing:
            print(f"  - {f}")
    else:
        print("[OK] Все критические файлы на месте")
    
    return len(missing) == 0

if __name__ == "__main__":
    print("Проверка файлов для GitHub...")
    print("=" * 60)
    check_files()

