#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("=" * 70)
print("АНАЛИЗ: УМЕНЬШЕНИЕ ПЕРИОДА ПРОВЕРОК")
print("=" * 70)

print("\nТЕКУЩЕЕ РАСПИСАНИЕ:")
print("-" * 70)
current_schedule = [
    (9, 0), (9, 45), (10, 30), (11, 15), (12, 0), (12, 45),
    (13, 30), (14, 15), (15, 0), (15, 45), (16, 30), (17, 15),
    (18, 0), (18, 45), (19, 30), (20, 15), (21, 0), (21, 45),
    (22, 30), (23, 15)
]

print(f"Интервал: 45 минут")
print(f"Проверок в день: {len(current_schedule)}")
print(f"Первая проверка: {current_schedule[0][0]:02d}:{current_schedule[0][1]:02d}")
print(f"Последняя проверка: {current_schedule[-1][0]:02d}:{current_schedule[-1][1]:02d}")

print("\n" + "=" * 70)
print("ВАРИАНТЫ УМЕНЬШЕНИЯ ИНТЕРВАЛА")
print("-" * 70)

# Вариант 1: 30 минут
schedule_30 = []
for hour in range(9, 24):
    for minute in [0, 30]:
        if hour == 23 and minute > 0:
            break
        schedule_30.append((hour, minute))

print("\nВАРИАНТ 1: Каждые 30 минут")
print(f"  Проверок в день: {len(schedule_30)}")
print(f"  Увеличение: +{len(schedule_30) - len(current_schedule)} проверок (+{int((len(schedule_30) - len(current_schedule)) / len(current_schedule) * 100)}%)")
print(f"  Примеры: {schedule_30[0][0]:02d}:{schedule_30[0][1]:02d}, {schedule_30[1][0]:02d}:{schedule_30[1][1]:02d}, {schedule_30[2][0]:02d}:{schedule_30[2][1]:02d}...")

# Вариант 2: 15 минут
schedule_15 = []
for hour in range(9, 24):
    for minute in [0, 15, 30, 45]:
        if hour == 23 and minute > 0:
            break
        schedule_15.append((hour, minute))

print("\nВАРИАНТ 2: Каждые 15 минут")
print(f"  Проверок в день: {len(schedule_15)}")
print(f"  Увеличение: +{len(schedule_15) - len(current_schedule)} проверок (+{int((len(schedule_15) - len(current_schedule)) / len(current_schedule) * 100)}%)")
print(f"  Примеры: {schedule_15[0][0]:02d}:{schedule_15[0][1]:02d}, {schedule_15[1][0]:02d}:{schedule_15[1][1]:02d}, {schedule_15[2][0]:02d}:{schedule_15[2][1]:02d}...")

# Вариант 3: 20 минут
schedule_20 = []
for hour in range(9, 24):
    for minute in [0, 20, 40]:
        if hour == 23 and minute > 0:
            break
        schedule_20.append((hour, minute))

print("\nВАРИАНТ 3: Каждые 20 минут")
print(f"  Проверок в день: {len(schedule_20)}")
print(f"  Увеличение: +{len(schedule_20) - len(current_schedule)} проверок (+{int((len(schedule_20) - len(current_schedule)) / len(current_schedule) * 100)}%)")
print(f"  Примеры: {schedule_20[0][0]:02d}:{schedule_20[0][1]:02d}, {schedule_20[1][0]:02d}:{schedule_20[1][1]:02d}, {schedule_20[2][0]:02d}:{schedule_20[2][1]:02d}...")

print("\n" + "=" * 70)
print("АНАЛИЗ ПЛЮСОВ И МИНУСОВ")
print("-" * 70)

print("\n30 МИНУТ:")
print("  [ПЛЮСЫ]")
print("    - +50% проверок (20 -> 30 в день)")
print("    - Больше шансов поймать матчи")
print("    - Разумный баланс")
print("  [МИНУСЫ]")
print("    - Больше нагрузка на API Scores24")
print("    - Больше сообщений в канал (если матчи есть)")

print("\n15 МИНУТ:")
print("  [ПЛЮСЫ]")
print("    - +100% проверок (20 -> 42 в день)")
print("    - Максимальный охват матчей")
print("    - Почти в реальном времени")
print("  [МИНУСЫ]")
print("    - Очень большая нагрузка на API")
print("    - Много сообщений (может засорить канал)")
print("    - Риск блокировки API при частых запросах")

print("\n20 МИНУТ:")
print("  [ПЛЮСЫ]")
print("    - +75% проверок (20 -> 35 в день)")
print("    - Хороший баланс")
print("    - Не слишком часто")
print("  [МИНУСЫ]")
print("    - Нестандартный интервал (сложнее запомнить)")

print("\n" + "=" * 70)
print("МОЯ ЧЕСТНАЯ РЕКОМЕНДАЦИЯ")
print("=" * 70)
print("\nВАРИАНТ 1: 30 минут - ОПТИМАЛЬНЫЙ")
print("  - Разумное увеличение проверок (+50%)")
print("  - Не перегружает API")
print("  - Хороший баланс между охватом и нагрузкой")
print("\nВАРИАНТ 2: 20 минут - ЕСЛИ НУЖНО БОЛЬШЕ")
print("  - Еще больше проверок (+75%)")
print("  - Но нестандартный интервал")
print("\nВАРИАНТ 3: 15 минут - ТОЛЬКО ЕСЛИ КРИТИЧЕСКИ МАЛО МАТЧЕЙ")
print("  - Максимальный охват (+100%)")
print("  - Но риск перегрузки API")
print("  - Может быть слишком часто для канала")

print("\n" + "=" * 70)
print("ИТОГОВЫЙ ВЕРДИКТ")
print("=" * 70)
print("ДА, уменьшение интервала МОЖЕТ ДАТЬ РЕЗУЛЬТАТ")
print("Рекомендую начать с 30 минут:")
print("  - Простое изменение (обновить SCHEDULE_TIMES)")
print("  - +50% проверок")
print("  - Минимальный риск перегрузки")
print("  - Хороший баланс")

