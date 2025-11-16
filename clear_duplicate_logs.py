#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

LOG_FILE = Path("data/recommendations_log.csv")

if not LOG_FILE.exists():
    print("Лог файл не найден. Нечего очищать.")
    exit(0)

# Читаем все записи
rows = []
with open(LOG_FILE, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    header = reader.fieldnames
    rows = list(reader)

print(f"Всего записей в логе: {len(rows)}")

# Фильтруем: оставляем только записи старше 4 часов
# Или записи, где telegram_message_id пустой (неудачная отправка)
now = datetime.now(ZoneInfo("Europe/Moscow"))
cutoff_time = now - timedelta(hours=4)

filtered_rows = []
removed_count = 0

for row in rows:
    timestamp_str = row.get("timestamp_msk", "")
    message_id = row.get("telegram_message_id", "")
    
    # Удаляем записи без message_id (неудачная отправка)
    if not message_id or message_id.strip() == "":
        removed_count += 1
        continue
    
    # Удаляем записи за последние 4 часа (те, что были записаны при ошибке)
    try:
        if timestamp_str:
            # Парсим timestamp (формат может быть разным)
            if ' ' in timestamp_str:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            else:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Делаем timezone-aware если нужно
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=ZoneInfo("Europe/Moscow"))
            
            # Если запись новее 4 часов - удаляем (это те, что были записаны при ошибке)
            if timestamp > cutoff_time:
                removed_count += 1
                continue
    except Exception:
        # Если не удалось распарсить - оставляем (старые записи)
        pass
    
    filtered_rows.append(row)

print(f"Удалено записей: {removed_count}")
print(f"Осталось записей: {len(filtered_rows)}")

# Записываем обратно
if header:
    with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(filtered_rows)
    print(f"\nЛог очищен. Удалено {removed_count} записей.")
else:
    print("Ошибка: не найден заголовок CSV")

