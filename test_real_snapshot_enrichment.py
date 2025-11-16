#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Тест обогащения на реальных данных"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_handball_analyzer import analyze_live_handball_matches
from scores24_snapshot_enricher import (
    get_scores24_snapshot_data,
    extract_minutes_from_snapshot,
    enrich_match_with_snapshot
)

# Используем MCP Browser функции из Cursor
try:
    # В контексте Cursor эти функции доступны
    mcp_browser_navigate = mcp_cursor-browser-extension_browser_navigate
    mcp_browser_wait = mcp_cursor-browser-extension_browser_wait_for
    mcp_browser_snapshot = mcp_cursor-browser-extension_browser_snapshot
    MCP_AVAILABLE = True
except NameError:
    print("⚠️ MCP Browser функции не доступны в этом контексте")
    print("   Запустите этот скрипт из Cursor с подключенным Browser MCP")
    MCP_AVAILABLE = False
    sys.exit(1)

print("=" * 80)
print("ТЕСТ ОБОГАЩЕНИЯ НА РЕАЛЬНЫХ ДАННЫХ")
print("=" * 80)

# Шаг 1: Получаем матчи через GraphQL
print("\n1️⃣ Получаем матчи через GraphQL (гандбол)...")
handball_matches = analyze_live_handball_matches(limit=10)
print(f"   Найдено матчей: {len(handball_matches)}")

if not handball_matches:
    print("   ❌ Нет live матчей для тестирования")
    sys.exit(0)

# Показываем матчи ДО обогащения
print("\n📊 МАТЧИ ДО ОБОГАЩЕНИЯ:")
for i, match in enumerate(handball_matches[:5], 1):
    teams = match.get("teams", ["?", "?"])
    score = match.get("score", "?:?")
    minute = match.get("minute_numeric")
    minute_str = match.get("minute", "None")
    print(f"   {i}. {teams[0]} vs {teams[1]}")
    print(f"      Счет: {score}")
    print(f"      Минута: {minute} ({minute_str})")
    print(f"      Slug: {match.get('slug', '?')[:50]}...")

# Шаг 2: Получаем snapshot
print("\n2️⃣ Получаем snapshot через Browser MCP...")
try:
    snapshot = get_scores24_snapshot_data(
        "handball",
        mcp_browser_navigate,
        mcp_browser_wait,
        mcp_browser_snapshot
    )
    print(f"   ✅ Snapshot получен")
    print(f"   Тип данных: {type(snapshot)}")
except Exception as e:
    print(f"   ❌ Ошибка получения snapshot: {e}")
    sys.exit(1)

# Шаг 3: Извлекаем минуты из snapshot
print("\n3️⃣ Извлекаем минуты из snapshot...")
minutes = extract_minutes_from_snapshot(snapshot, "handball")
print(f"   Найдено минут: {len(minutes)}")
if minutes:
    print("   Примеры:")
    for slug, minute in list(minutes.items())[:5]:
        print(f"      {slug[:50]}... → {minute} мин")

# Шаг 4: Обогащаем матчи
print("\n4️⃣ Обогащаем матчи данными из snapshot...")
enriched_matches = []
for match in handball_matches[:5]:
    enriched = enrich_match_with_snapshot(match, minutes)
    enriched_matches.append(enriched)

# Шаг 5: Показываем результаты
print("\n📊 МАТЧИ ПОСЛЕ ОБОГАЩЕНИЯ:")
enriched_count = 0
for i, match in enumerate(enriched_matches, 1):
    teams = match.get("teams", ["?", "?"])
    score = match.get("score", "?:?")
    minute_before = handball_matches[i-1].get("minute_numeric")
    minute_after = match.get("minute_numeric")
    minute_source = match.get("minute_source", "graphql")
    
    was_enriched = minute_before is None and minute_after is not None
    
    print(f"   {i}. {teams[0]} vs {teams[1]}")
    print(f"      Счет: {score}")
    print(f"      Минута ДО: {minute_before}")
    print(f"      Минута ПОСЛЕ: {minute_after} (источник: {minute_source})")
    if was_enriched:
        print(f"      ✅ ОБОГАЩЕНО!")
        enriched_count += 1
    print()

# Итоги
print("=" * 80)
print("ИТОГИ:")
print(f"   Всего матчей проверено: {len(enriched_matches)}")
print(f"   Обогащено минут: {enriched_count}")
print(f"   Минут найдено в snapshot: {len(minutes)}")
print("=" * 80)

