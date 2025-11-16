"""Проверка работы планировщика и механизма блокировки"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("ПРОВЕРКА ПЛАНИРОВЩИКА И МЕХАНИЗМА БЛОКИРОВКИ")
print("=" * 60)

# Проверка lock файла
lock_file = ".auto_cycle.lock"
lock_exists = os.path.exists(lock_file)
print(f"\n1. Lock файл (.auto_cycle.lock):")
print(f"   Существует: {lock_exists}")

if lock_exists:
    try:
        with open(lock_file, 'r') as f:
            pid = f.read().strip()
        print(f"   PID в файле: {pid}")
        
        # Проверяем, жив ли процесс
        try:
            os.kill(int(pid), 0)  # Проверка без сигнала
            print(f"   Процесс {pid} активен")
        except (OSError, ValueError):
            print(f"   Процесс {pid} НЕ активен (можно удалить lock файл)")
    except Exception as e:
        print(f"   Ошибка чтения: {e}")

# Механизм блокировки
print("\n2. Механизм блокировки:")
print("   - При запуске планировщик создаёт .auto_cycle.lock")
print("   - Если файл уже существует, второй процесс завершается")
print("   - Это предотвращает конфликты и дублирование сообщений")

# Рекомендации
print("\n3. Рекомендации:")
if not lock_exists:
    print("   ⚠️  Планировщик не запущен (lock файла нет)")
    print("   → Запустите: python auto_cycle_scheduler.py")
    print("   → Или через: start_scheduler.bat")
else:
    print("   ✅ Планировщик работает (lock файл существует)")
    print("   → Не запускайте второй экземпляр - он автоматически завершится")

print("\n" + "=" * 60)

