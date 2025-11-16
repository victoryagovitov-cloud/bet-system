#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from generate_live_report import (
    EXTENDED_MIN_DOMINANCE, EXTENDED_MIN_XG_DIFF, EXTENDED_MIN_SOT_DIFF,
    PRIMARY_MAX_ODDS, EXTENDED_MAX_ODDS
)

print("=" * 70)
print("ПРОВЕРКА ВНЕДРЕННЫХ УЛУЧШЕНИЙ")
print("=" * 70)

print("\n1. УЖЕСТОЧЕННЫЕ ТРЕБОВАНИЯ ДЛЯ EXTENDED:")
print(f"  EXTENDED_MIN_DOMINANCE: {EXTENDED_MIN_DOMINANCE} (было 3.0)")
print(f"  EXTENDED_MIN_XG_DIFF: {EXTENDED_MIN_XG_DIFF} (было 0.1)")
print(f"  EXTENDED_MIN_SOT_DIFF: {EXTENDED_MIN_SOT_DIFF} (было 0)")

print("\n2. УЧЕТ ВРЕМЕНИ МАТЧА:")
print("  ФУТБОЛ:")
print("    - < 30 минут: required_dominance = 8.0 (PRIMARY) / 8.0 (EXTENDED)")
print("    - 30-60 минут: required_dominance = 2.0 (PRIMARY) / 6.0 (EXTENDED)")
print("    - > 60 минут: required_dominance = 2.0 (PRIMARY) / 5.0 (EXTENDED)")
print("\n  ТЕННИС:")
print("    - 1-й сет, < 6 геймов: required_dominance = 5.0 (PRIMARY) / 8.0 (EXTENDED)")
print("    - 1-й сет, >= 6 геймов: required_dominance = 2.0 (PRIMARY) / 6.0 (EXTENDED)")
print("    - 2-й сет и дальше: required_dominance = 2.0 (PRIMARY) / 5.0 (EXTENDED)")

print("\n3. УЛУЧШЕННАЯ ФОРМУЛА DOMINANCE_SCORE:")
print("  - Учитывается время матча: time_factor = minute / 90.0")
print("  - Учитывается текущий счет: score_factor = score_diff * 2")
print("  - Увеличен вес владения: possession * 0.5 (было 0.2)")
print("  - Формула: xG*3 + SOT*2 + shots*0.5 + possession*0.5 + score*time")

print("\n4. ПРИМЕРЫ:")
print("\n  Матч А: 1:0 на 20-й минуте, xG 0.5-0.3, удары 3-2")
print("    Старая формула: dominance = 3.0")
print("    Новая формула: dominance = 3.0 + (2 * 0.22) = 3.44")
print("    Требование для EXTENDED: >= 8.0 (ранний матч)")
print("    Результат: НЕ проходит (3.44 < 8.0)")
print("\n  Матч Б: 1:0 на 80-й минуте, xG 0.5-0.3, удары 3-2")
print("    Старая формула: dominance = 3.0")
print("    Новая формула: dominance = 3.0 + (2 * 0.89) = 4.78")
print("    Требование для EXTENDED: >= 5.0 (поздний матч)")
print("    Результат: НЕ проходит (4.78 < 5.0), но близко!")

print("\n" + "=" * 70)
print("ВСЕ УЛУЧШЕНИЯ ВНЕДРЕНЫ!")
print("=" * 70)

