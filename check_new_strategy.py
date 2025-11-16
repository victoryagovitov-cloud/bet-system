#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from generate_live_report import (
    MIN_ODDS, PRIMARY_MAX_ODDS, EXTENDED_MAX_ODDS,
    EXTENDED_MIN_DOMINANCE, EXTENDED_MIN_XG_DIFF, EXTENDED_MIN_SOT_DIFF
)

print("=" * 70)
print("НОВАЯ СТРАТЕГИЯ ОТБОРА МАТЧЕЙ")
print("=" * 70)

print(f"\nДИАПАЗОНЫ КОЭФФИЦИЕНТОВ:")
print(f"  Минимум: {MIN_ODDS}")
print(f"  PRIMARY (безопасные): 1.01 - {PRIMARY_MAX_ODDS}")
print(f"  EXTENDED (интересные): {PRIMARY_MAX_ODDS + 0.01:.2f} - {EXTENDED_MAX_ODDS}")

print(f"\nТРЕБОВАНИЯ ДЛЯ EXTENDED TIER:")
print(f"  Минимальный dominance: {EXTENDED_MIN_DOMINANCE}")
print(f"  Минимальная разница xG: {EXTENDED_MIN_XG_DIFF}")
print(f"  Минимальная разница ударов в створ: {EXTENDED_MIN_SOT_DIFF}")

print(f"\nКОЛИЧЕСТВО МАТЧЕЙ В СООБЩЕНИИ:")
print(f"  По умолчанию: 5 матчей (было 3)")

print(f"\nСТРАТЕГИЯ:")
print(f"  1. Безопасные матчи (1.01-1.10): идеальная статистика, 100% варианты")
print(f"  2. Интересные матчи (1.11-1.50): сниженные требования, но все еще надежные")
print(f"  3. Приоритет более высоким коэффициентам при сортировке")
print(f"  4. Больше матчей в сообщении для разнообразия")

print(f"\nЦЕЛЬ:")
print(f"  - Поднять средний коэффициент до ~1.2-1.3")
print(f"  - Привлечь аудиторию интересными вариантами")
print(f"  - Сохранить надежность через безопасные матчи")

print("=" * 70)

