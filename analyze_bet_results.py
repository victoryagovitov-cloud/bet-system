#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from collections import defaultdict
from pathlib import Path

RESULTS_FILE = Path("data/recommendations_results.csv")

stats = {
    "total": 0,
    "wins": 0,
    "losses": 0,
    "pending": 0,
    "coefficients": [],
    "win_coefficients": [],
    "loss_coefficients": [],
    "profit_total": 0.0,
    "by_sport": defaultdict(lambda: {"wins": 0, "losses": 0, "total": 0}),
}

if RESULTS_FILE.exists():
    with RESULTS_FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats["total"] += 1
            
            status = row.get("result", "").lower()
            coef_str = row.get("coefficient", "")
            profit_str = row.get("profit_units", "")
            
            if coef_str:
                try:
                    coef = float(coef_str)
                    stats["coefficients"].append(coef)
                    
                    if status == "win":
                        stats["wins"] += 1
                        stats["win_coefficients"].append(coef)
                    elif status == "loss":
                        stats["losses"] += 1
                        stats["loss_coefficients"].append(coef)
                    else:
                        stats["pending"] += 1
                except:
                    pass
            
            if profit_str:
                try:
                    profit = float(profit_str)
                    stats["profit_total"] += profit
                except:
                    pass

# Данные из скриншотов (выигрышные ставки, которые ты показывал)
screenshots_data = [
    {"sport": "tennis", "coef": 1.01, "result": "win", "description": "Штебе С.-М. vs Хара Френд Д. Д."},
    {"sport": "tennis", "coef": 1.2, "result": "win", "description": "Кестельбойм М./Дюран Г. vs Демолинер М./Баррьентос Н."},
    {"sport": "football", "coef": 1.1, "result": "win", "description": "Вест Хэм (Ж) vs Саутгемптон (Ж)"},
    {"sport": "tennis", "coef": 1.06, "result": "win", "description": "Синнер Я. vs Зверев А."},
]

print("=" * 60)
print("СТАТИСТИКА ПО СКРИНАМ ИЗ BETBOOM")
print("=" * 60)

print("\nДАННЫЕ ИЗ СКРИНШОТОВ (выигрышные ставки):")
print(f"Всего ставок из скриншотов: {len(screenshots_data)}")

screenshot_coefs = [s["coef"] for s in screenshots_data]
if screenshot_coefs:
    print(f"\nКоэффициенты из скриншотов:")
    print(f"  Средний: {sum(screenshot_coefs)/len(screenshot_coefs):.2f}")
    print(f"  Мин: {min(screenshot_coefs):.2f}")
    print(f"  Макс: {max(screenshot_coefs):.2f}")

print("\nДетали ставок:")
for i, bet in enumerate(screenshots_data, 1):
    print(f"  {i}. {bet['description']}")
    print(f"     Кэф: {bet['coef']:.2f}, Результат: {bet['result']}")

if stats["total"] > 0:
    print(f"\nДАННЫЕ ИЗ СИСТЕМЫ (recommendations_results.csv):")
    print(f"Всего ставок: {stats['total']}")
    print(f"Выигрышных: {stats['wins']}")
    print(f"Проигрышных: {stats['losses']}")
    print(f"В ожидании: {stats['pending']}")
    
    if stats["coefficients"]:
        print(f"\nКоэффициенты (из системы):")
        print(f"  Средний: {sum(stats['coefficients'])/len(stats['coefficients']):.2f}")
        print(f"  Мин: {min(stats['coefficients']):.2f}")
        print(f"  Макс: {max(stats['coefficients']):.2f}")
    
    if stats["win_coefficients"]:
        print(f"\nКоэффициенты выигрышных:")
        print(f"  Средний: {sum(stats['win_coefficients'])/len(stats['win_coefficients']):.2f}")
        print(f"  Мин: {min(stats['win_coefficients']):.2f}")
        print(f"  Макс: {max(stats['win_coefficients']):.2f}")
    
    if stats["loss_coefficients"]:
        print(f"\nКоэффициенты проигрышных:")
        print(f"  Средний: {sum(stats['loss_coefficients'])/len(stats['loss_coefficients']):.2f}")
        print(f"  Мин: {min(stats['loss_coefficients']):.2f}")
        print(f"  Макс: {max(stats['loss_coefficients']):.2f}")
    
    if stats["wins"] + stats["losses"] > 0:
        win_rate = (stats["wins"] / (stats["wins"] + stats["losses"])) * 100
        print(f"\nПроцент выигрышей: {win_rate:.1f}%")
    
    if stats["profit_total"] != 0:
        print(f"\nОбщий профит: {stats['profit_total']:.2f} единиц")

print("\n" + "=" * 60)
print("ВАЖНО:")
print("Для полной статистики нужны данные о ВСЕХ ставках")
print("(и выигрышных, и проигрышных) из твоей истории BetBoom.")
print("=" * 60)

