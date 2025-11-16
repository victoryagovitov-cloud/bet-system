#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматический запуск полного цикла анализа по сигналу 🎯F
"""

import sys
import os
import subprocess
import time
from datetime import datetime

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

print("\n" + "="*80)
print("🚀 АВТОМАТИЧЕСКИЙ ЦИКЛ АНАЛИЗА")
print("="*80 + "\n")

# ШАГ 1: Запускаем парсер
print("⏳ Запускаю парсер снимков...")

try:
    result = subprocess.run(
        [sys.executable, "parse_snapshot_final.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=60
    )
    
    print(result.stdout)
    
    if result.returncode != 0 and result.stderr:
        print(f"⚠️ Предупреждение: {result.stderr}")
    
    print("\n✅ ЦИКЛ ЗАВЕРШЕН\n")
    
except subprocess.TimeoutExpired:
    print("❌ Превышен тайм-аут (60 сек)\n")
except Exception as e:
    print(f"❌ Ошибка: {e}\n")

