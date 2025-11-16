#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess

print("=" * 60)
print("ПРОВЕРКА ПЛАНИРОВЩИКА")
print("=" * 60)

# Проверка lock файла планировщика
lock_file = ".auto_cycle.lock"
if os.path.exists(lock_file):
    print(f"\n[OK] Lock файл планировщика существует: {lock_file}")
    try:
        with open(lock_file, 'r') as f:
            pid = f.read().strip()
            print(f"  PID из lock файла: {pid}")
    except Exception as e:
        print(f"  [ОШИБКА] Не удалось прочитать lock файл: {e}")
else:
    print(f"\n[FAIL] Lock файл планировщика НЕ существует: {lock_file}")

# Проверка процессов Python
print("\nПроцессы Python:")
try:
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                          capture_output=True, text=True, encoding='cp866')
    lines = result.stdout.split('\n')
    python_processes = [line for line in lines if 'python.exe' in line.lower() and 'PID' not in line]
    
    if python_processes:
        print(f"  Найдено процессов: {len(python_processes)}")
        for line in python_processes[:10]:
            parts = line.split()
            if len(parts) >= 2:
                print(f"    PID: {parts[1]}")
    else:
        print("  [FAIL] Процессы Python не найдены")
except Exception as e:
    print(f"  [ОШИБКА] Не удалось проверить процессы: {e}")

# Проверка watchdog
watchdog_lock = ".watchdog.lock"
if os.path.exists(watchdog_lock):
    print(f"\n[OK] Watchdog lock файл существует: {watchdog_lock}")
    try:
        with open(watchdog_lock, 'r') as f:
            pid = f.read().strip()
            print(f"  PID из lock файла: {pid}")
    except Exception as e:
        print(f"  [ОШИБКА] Не удалось прочитать lock файл: {e}")
else:
    print(f"\n[FAIL] Watchdog lock файл НЕ существует: {watchdog_lock}")

print("\n" + "=" * 60)
