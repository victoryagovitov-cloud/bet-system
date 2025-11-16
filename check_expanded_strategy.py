#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from generate_live_report import (
    MIN_ODDS, PRIMARY_MAX_ODDS, EXTENDED_MAX_ODDS,
    EXTENDED_MIN_DOMINANCE, EXTENDED_MIN_XG_DIFF, EXTENDED_MIN_SOT_DIFF
)

print("=" * 70)
print("РАСШИРЕННАЯ СТРАТЕГИЯ - АНАЛИЗ ВСЕХ МАТЧЕЙ С СТАТИСТИКОЙ")
print("=" * 70)

print(f"\nДИАПАЗОНЫ КОЭФФИЦИЕНТОВ:")
print(f"  Минимум: {MIN_ODDS}")
print(f"  PRIMARY (безопасные): 1.01 - {PRIMARY_MAX_ODDS}")
print(f"  EXTENDED (интересные): {PRIMARY_MAX_ODDS + 0.01:.2f} - {EXTENDED_MAX_ODDS}")

print(f"\nМИНИМАЛЬНЫЕ ТРЕБОВАНИЯ (анализируем все с хоть какой-то статистикой):")
print(f"  Минимальный dominance: {EXTENDED_MIN_DOMINANCE} (было 8.0)")
print(f"  Минимальная разница xG: {EXTENDED_MIN_XG_DIFF} (было 0.25)")
print(f"  Минимальная разница ударов в створ: {EXTENDED_MIN_SOT_DIFF} (было 1)")

print(f"\nФИЛЬТРАЦИЯ:")
print(f"  - Отфильтровываем только явных аутсайдеров (dominance < -5.0)")
print(f"  - Анализируем все матчи с хоть каким-то перевесом")
print(f"  - Для PRIMARY: dominance > 0 ИЛИ (xG >= 0 И удары >= 0)")
print(f"  - Для EXTENDED: dominance >= {EXTENDED_MIN_DOMINANCE} ИЛИ минимальные показатели ИЛИ (перевес + кэф >= 1.15)")

print(f"\nПОИСК МАТЧЕЙ:")
print(f"  - Ищем в 2 раза больше матчей для разнообразия")
print(f"  - Возвращаем в 2 раза больше кандидатов из каждой функции")
print(f"  - Финальный отбор: до 5 матчей с приоритетом более высоким коэффициентам")

print(f"\nЦЕЛЬ:")
print(f"  - Сделать канал живым - больше матчей в день")
print(f"  - Анализировать все матчи с хоть какой-то статистикой на Scores24")
print(f"  - Поднять средний коэффициент до 1.2-1.3")
print(f"  - Сохранить качество через приоритизацию")

print("=" * 70)

