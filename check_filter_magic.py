#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from generate_live_report import (
    EXTENDED_MIN_DOMINANCE, EXTENDED_MIN_XG_DIFF, EXTENDED_MIN_SOT_DIFF,
    PRIMARY_MAX_ODDS, EXTENDED_MAX_ODDS
)

print("=" * 70)
print("МАГИЯ В НАСТРОЙКАХ ФИЛЬТРОВ")
print("=" * 70)

print("\nШАГ 1: АНАЛИЗИРУЕМ ВСЕ МАТЧИ С СТАТИСТИКОЙ")
print("  - Ищем все live матчи на Scores24")
print("  - Проверяем наличие статистики (xG, удары, владение)")
print("  - Отфильтровываем только явных аутсайдеров (dominance < -5.0)")

print("\nШАГ 2: ПРИМЕНЯЕМ УМНЫЕ ФИЛЬТРЫ (ВОТ ГДЕ МАГИЯ!)")
print("-" * 70)

print("\nPRIMARY TIER (кэфы 1.01-1.10):")
print("  - < 30 минут: dominance >= 5.0")
print("  - >= 30 минут: dominance >= 2.0 ИЛИ (xG >= 0.2 И удары >= 1)")
print("  Цель: Безопасные матчи с реальным перевесом")

print("\nEXTENDED TIER (кэфы 1.11-1.50):")
print(f"  - < 30 минут: dominance >= 8.0")
print(f"  - 30-60 минут: dominance >= {EXTENDED_MIN_DOMINANCE}")
print(f"  - > 60 минут: dominance >= 5.0")
print(f"  - ИЛИ (xG >= {EXTENDED_MIN_XG_DIFF} И удары >= {EXTENDED_MIN_SOT_DIFF} И минута >= 60)")
print("  Цель: Интересные матчи, но все еще надежные")

print("\nШАГ 3: ПРИОРИТИЗАЦИЯ")
print("  - Сортируем по коэффициентам (выше = лучше)")
print("  - Затем по dominance")
print("  - Отбираем топ-5 матчей")

print("\n" + "=" * 70)
print("КЛЮЧЕВЫЕ НАСТРОЙКИ (МАГИЯ):")
print("-" * 70)
print(f"EXTENDED_MIN_DOMINANCE = {EXTENDED_MIN_DOMINANCE}")
print(f"EXTENDED_MIN_XG_DIFF = {EXTENDED_MIN_XG_DIFF}")
print(f"EXTENDED_MIN_SOT_DIFF = {EXTENDED_MIN_SOT_DIFF}")
print("\nЭти числа определяют:")
print("  - Сколько матчей пройдет фильтры")
print("  - Качество отбора")
print("  - Процент выигрышей")
print("\nИзменяя эти числа, мы контролируем баланс:")
print("  - Меньше = больше матчей, но ниже качество")
print("  - Больше = меньше матчей, но выше качество")

print("\n" + "=" * 70)
print("СИСТЕМА РАБОТАЕТ ТАК:")
print("-" * 70)
print("1. Анализируем ВСЕ матчи с статистикой (широкий поиск)")
print("2. Применяем УМНЫЕ ФИЛЬТРЫ (настройки коэффициентов)")
print("3. Приоритизируем по коэффициентам и dominance")
print("4. Отбираем лучшие матчи")
print("\nВся магия - в настройках фильтров!")
print("=" * 70)

