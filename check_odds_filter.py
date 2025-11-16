#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from generate_live_report import MIN_ODDS, PRIMARY_MAX_ODDS, EXTENDED_MAX_ODDS

print("=" * 60)
print("НАСТРОЙКИ ФИЛЬТРАЦИИ ПО КОЭФФИЦИЕНТАМ")
print("=" * 60)
print(f"\nМинимальный коэффициент (MIN_ODDS): {MIN_ODDS}")
print(f"Максимальный для primary tier: {PRIMARY_MAX_ODDS}")
print(f"Максимальный для extended tier: {EXTENDED_MAX_ODDS}")
print(f"\nДиапазон коэффициентов: {MIN_ODDS} - {EXTENDED_MAX_ODDS}")
print(f"\nТеперь будут отбираться только матчи с коэффициентами >= {MIN_ODDS}")
print("Это должно поднять средний коэффициент до ~1.2")
print("=" * 60)

