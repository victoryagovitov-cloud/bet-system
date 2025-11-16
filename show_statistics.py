#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("data/recommendations_log.csv")

if not LOG_FILE.exists():
    print("Файл лога не найден:", LOG_FILE)
    exit(1)

stats = {
    "total": 0,
    "by_sport": defaultdict(int),
    "by_date": defaultdict(int),
    "coefficients": [],
    "probabilities": [],
    "dominance_scores": [],
    "messages_sent": set(),
}

with LOG_FILE.open("r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        stats["total"] += 1
        
        sport = row.get("sport", "unknown")
        # Пропускаем если это не вид спорта (например, message_id)
        if sport and sport not in ["football", "tennis", "handball"] and sport.isdigit():
            continue
        stats["by_sport"][sport] += 1
        
        timestamp = row.get("timestamp_msk", "")
        if timestamp:
            try:
                date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").date()
                stats["by_date"][date] += 1
            except:
                pass
        
        msg_id = row.get("telegram_message_id", "")
        if msg_id:
            stats["messages_sent"].add(msg_id)
        
        coef = row.get("coefficient", "")
        if coef:
            try:
                coef_val = float(coef)
                # Фильтруем нереалистичные коэффициенты (больше 10)
                if 0.5 <= coef_val <= 10.0:
                    stats["coefficients"].append(coef_val)
            except:
                pass
        
        prob = row.get("probability_percent", "")
        if prob:
            try:
                stats["probabilities"].append(float(prob))
            except:
                pass
        
        dom = row.get("dominance_score", "")
        if dom:
            try:
                stats["dominance_scores"].append(float(dom))
            except:
                pass

print("=" * 60)
print("СТАТИСТИКА РЕКОМЕНДАЦИЙ")
print("=" * 60)

print(f"\nВсего рекомендаций: {stats['total']}")
print(f"Уникальных сообщений отправлено: {len(stats['messages_sent'])}")

print("\nПо видам спорта:")
for sport, count in sorted(stats["by_sport"].items(), key=lambda x: -x[1]):
    print(f"  {sport}: {count}")

print("\nПо датам (последние 7 дней):")
recent_dates = sorted(stats["by_date"].items(), reverse=True)[:7]
for date, count in recent_dates:
    print(f"  {date}: {count} рекомендаций")

if stats["coefficients"]:
    print(f"\nКоэффициенты:")
    print(f"  Всего: {len(stats['coefficients'])}")
    print(f"  Средний: {sum(stats['coefficients'])/len(stats['coefficients']):.2f}")
    print(f"  Мин: {min(stats['coefficients']):.2f}")
    print(f"  Макс: {max(stats['coefficients']):.2f}")

if stats["probabilities"]:
    print(f"\nВероятности:")
    print(f"  Всего: {len(stats['probabilities'])}")
    print(f"  Средняя: {sum(stats['probabilities'])/len(stats['probabilities']):.1f}%")
    print(f"  Мин: {min(stats['probabilities']):.1f}%")
    print(f"  Макс: {max(stats['probabilities']):.1f}%")

if stats["dominance_scores"]:
    print(f"\nDominance Score:")
    print(f"  Всего: {len(stats['dominance_scores'])}")
    print(f"  Средний: {sum(stats['dominance_scores'])/len(stats['dominance_scores']):.2f}")
    print(f"  Мин: {min(stats['dominance_scores']):.2f}")
    print(f"  Макс: {max(stats['dominance_scores']):.2f}")

print("\n" + "=" * 60)
print("ПРИМЕЧАНИЕ: Это статистика отправленных рекомендаций.")
print("Для статистики выигрышей/проигрышей нужны данные о результатах ставок.")
print("=" * 60)

