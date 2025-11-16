#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Реальный прогон с обогащением через snapshot"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from generate_live_report import generate_live_report

print("=" * 80)
print("РЕАЛЬНЫЙ ПРОГОН С ОБОГАЩЕНИЕМ ЧЕРЕЗ SNAPSHOT")
print("=" * 80)

# Используем MCP Browser функции
try:
    # В контексте Cursor эти функции доступны
    report, matches, meta = generate_live_report(
        max_matches=5,
        mcp_browser_navigate=mcp_cursor-browser-extension_browser_navigate,
        mcp_browser_wait=mcp_cursor-browser-extension_browser_wait_for,
        mcp_browser_snapshot=mcp_cursor-browser-extension_browser_snapshot
    )
    
    print("\n" + "=" * 80)
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
            
            print(f"\n{i}. {teams[0]} vs {teams[1]} ({sport})")
            print(f"   Минута: {minute} (источник: {minute_source})")
            print(f"   Вероятность: {probability}%")
            if minute_source == "snapshot":
                print(f"   ✅ ОБОГАЩЕНО через snapshot!")
    
    print("\n" + "=" * 80)
    print("ОТЧЕТ:")
    print("=" * 80)
    print(report)
    
except NameError:
    print("\n⚠️ MCP Browser функции не доступны в этом контексте")
    print("   Запускаю БЕЗ обогащения...")
    
    report, matches, meta = generate_live_report(max_matches=5)
    
    print("\n" + "=" * 80)
    print("РЕЗУЛЬТАТ (БЕЗ обогащения):")
    print("=" * 80)
    print(f"\nНайдено матчей: {len(matches)}")
    print("\nОТЧЕТ:")
    print(report)

