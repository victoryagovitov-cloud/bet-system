#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Реальный прогон с обогащением - использует MCP Browser инструменты"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from generate_live_report import generate_live_report

# Обертки для MCP Browser функций
def mcp_navigate(url):
    """Обертка для browser_navigate"""
    # В реальном контексте это будет вызывать mcp_cursor-browser-extension_browser_navigate
    # Здесь используем заглушку для теста
    pass

def mcp_wait(**kwargs):
    """Обертка для browser_wait_for"""
    pass

def mcp_snapshot():
    """Обертка для browser_snapshot"""
    return {}

print("=" * 80)
print("РЕАЛЬНЫЙ ПРОГОН С ОБОГАЩЕНИЕМ")
print("=" * 80)
print("\nЗапускаю generate_live_report...")
print("(Для полного обогащения нужны реальные MCP Browser функции)")
print()

# Запускаем без обогащения (MCP функции - заглушки)
report, matches, meta = generate_live_report(
    max_matches=5,
    mcp_browser_navigate=mcp_navigate,
    mcp_browser_wait=mcp_wait,
    mcp_browser_snapshot=mcp_snapshot
)

print("=" * 80)
print("РЕЗУЛЬТАТ:")
print("=" * 80)
print(f"\nНайдено матчей: {len(matches)}")

if matches:
    print("\nДЕТАЛИ МАТЧЕЙ:")
    for i, match in enumerate(matches, 1):
        teams = match.get("teams", ["?", "?"])
        sport = match.get("sport", "?")
        minute = match.get("minute_numeric")
        minute_source = match.get("minute_source", "graphql")
        probability = match.get("estimated_probability", "?")
        odds = match.get("odds_info")
        odds_value = odds.value if odds else "?"
        
        print(f"\n{i}. {teams[0]} vs {teams[1]} ({sport})")
        print(f"   Минута: {minute} (источник: {minute_source})")
        print(f"   Вероятность: {probability}%")
        print(f"   Коэффициент: {odds_value}")
        if minute_source == "snapshot":
            print(f"   [ОБОГАЩЕНО через snapshot]")

print("\n" + "=" * 80)
print("ОТЧЕТ:")
print("=" * 80)
print(report)

