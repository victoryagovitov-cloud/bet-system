#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Тест через generate_live_report с MCP Browser"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 80)
print("ТЕСТ ЧЕРЕЗ generate_live_report")
print("=" * 80)

print("\n📋 Этот тест нужно запустить в контексте Cursor с MCP Browser")
print("   Используйте следующий код:\n")

print("""
from generate_live_report import generate_live_report

# Получаем отчет БЕЗ обогащения (как сейчас)
report1, matches1, meta1 = generate_live_report(max_matches=3)
print("БЕЗ обогащения:")
print(f"Матчей: {len(matches1)}")
for m in matches1:
    print(f"  {m.get('teams', ['?', '?'])[0]} vs {m.get('teams', ['?', '?'])[1]}")
    print(f"    Минута: {m.get('minute_numeric')} (источник: {m.get('minute_source', 'graphql')})")

# Получаем отчет С обогащением (если MCP Browser доступен)
try:
    report2, matches2, meta2 = generate_live_report(
        max_matches=3,
        mcp_browser_navigate=mcp_cursor-browser-extension_browser_navigate,
        mcp_browser_wait=mcp_cursor-browser-extension_browser_wait_for,
        mcp_browser_snapshot=mcp_cursor-browser-extension_browser_snapshot
    )
    print("\\nС обогащением:")
    print(f"Матчей: {len(matches2)}")
    for m in matches2:
        print(f"  {m.get('teams', ['?', '?'])[0]} vs {m.get('teams', ['?', '?'])[1]}")
        print(f"    Минута: {m.get('minute_numeric')} (источник: {m.get('minute_source', 'graphql')})")
except NameError:
    print("\\n⚠️ MCP Browser функции не доступны")
""")

print("\n" + "=" * 80)
print("АЛЬТЕРНАТИВНО: Протестируем напрямую через MCP Browser инструменты")
print("=" * 80)

