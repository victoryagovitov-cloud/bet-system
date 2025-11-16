"""Проверка запущенных процессов Python"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import subprocess

print("Проверка запущенных процессов Python:\n")

try:
    result = subprocess.run(
        ['powershell', '-Command', 
         'Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    print(result.stdout)
except Exception as e:
    print(f"Ошибка: {e}")

print(f"\nПроверка lock файла:")
lock_exists = os.path.exists('.auto_cycle.lock')
print(f"  .auto_cycle.lock существует: {lock_exists}")

if lock_exists:
    try:
        with open('.auto_cycle.lock', 'r') as f:
            pid = f.read().strip()
            print(f"  PID в lock файле: {pid}")
    except Exception as e:
        print(f"  Ошибка чтения: {e}")

print(f"\nТекущий PID: {os.getpid()}")

