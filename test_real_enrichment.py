#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Тест обогащения на реальных данных - использует MCP Browser инструменты"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_handball_analyzer import analyze_live_handball_matches
from scores24_snapshot_enricher import (
    extract_minutes_from_snapshot,
    enrich_match_with_snapshot
)

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
matches_before = []
for i, match in enumerate(handball_matches[:5], 1):
    teams = match.get("teams", ["?", "?"])
    score = match.get("score", "?:?")
    minute = match.get("minute_numeric")
    minute_str = match.get("minute", "None")
    slug = match.get("slug", "?")
    print(f"   {i}. {teams[0]} vs {teams[1]}")
    print(f"      Счет: {score}")
    print(f"      Минута: {minute} ({minute_str})")
    print(f"      Slug: {slug[:60]}...")
    matches_before.append({
        "teams": teams,
        "score": score,
        "minute": minute,
        "slug": slug
    })

print("\n" + "=" * 80)
print("⚠️  Для получения snapshot нужно использовать MCP Browser инструменты")
print("   Следующий шаг: получить snapshot через mcp_cursor-browser-extension_browser_snapshot")
print("=" * 80)

print("\n📋 ИНСТРУКЦИЯ:")
print("   1. Используйте MCP Browser для навигации на:")
print("      https://scores24.live/ru/handball?matchesFilter=live")
print("   2. Получите snapshot")
print("   3. Передайте snapshot в extract_minutes_from_snapshot()")
print("   4. Обогатите матчи через enrich_match_with_snapshot()")

print("\n💡 Для автоматического тестирования используйте generate_live_report()")
print("   с передачей MCP Browser функций")

