#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Тест обогащения данных через snapshot"""

# Этот файл будет использоваться в контексте Cursor с MCP Browser
# Показываю структуру, как это должно работать

print("=" * 60)
print("ТЕСТ ОБОГАЩЕНИЯ ДАННЫХ ЧЕРЕЗ SNAPSHOT")
print("=" * 60)

print("\nПЛАН:")
print("1. Получить матчи через GraphQL (как сейчас)")
print("2. Для матчей без минуты/сетов - получить snapshot Scores24")
print("3. Извлечь минуты/сеты из snapshot")
print("4. Обогатить данные матчей")

print("\nРЕАЛИЗАЦИЯ:")
print("""
# В generate_live_report.py добавить:

from scores24_snapshot_enricher import (
    get_scores24_snapshot_data,
    extract_minutes_from_snapshot,
    extract_tennis_sets_from_snapshot,
    enrich_match_with_snapshot
)

def enrich_matches_with_snapshot(
    matches: List[Dict],
    sport: str,
    mcp_browser_navigate=None,
    mcp_browser_wait=None,
    mcp_browser_snapshot=None
):
    # Проверяем, нужен ли snapshot
    needs_snapshot = any(
        m.get("minute_numeric") is None or 
        (sport == "tennis" and not m.get("completed_sets"))
        for m in matches
    )
    
    if not needs_snapshot:
        return matches
    
    if not all([mcp_browser_navigate, mcp_browser_wait, mcp_browser_snapshot]):
        return matches  # Без MCP Browser не можем обогатить
    
    # Получаем snapshot
    snapshot = get_scores24_snapshot_data(
        sport,
        mcp_browser_navigate,
        mcp_browser_wait,
        mcp_browser_snapshot
    )
    
    # Извлекаем данные
    minutes = extract_minutes_from_snapshot(snapshot, sport)
    sets = None
    if sport == "tennis":
        sets = extract_tennis_sets_from_snapshot(snapshot)
    
    # Обогащаем матчи
    enriched = []
    for match in matches:
        enriched.append(enrich_match_with_snapshot(match, minutes, sets))
    
    return enriched
""")

print("\nПРЕИМУЩЕСТВА:")
print("   - Получаем минуты для гандбола (сейчас их нет)")
print("   - Получаем завершенные сеты для тенниса")
print("   - Не ломаем существующую логику (GraphQL остается основным источником)")
print("   - Snapshot используется только для дополнения")

print("\nВАЖНО:")
print("   - Snapshot медленнее GraphQL (нужно время на загрузку страницы)")
print("   - Использовать только для матчей, где данных не хватает")
print("   - Кэшировать snapshot на несколько секунд")

