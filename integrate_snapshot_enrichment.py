#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Интеграция обогащения через snapshot в generate_live_report.py
Показывает, как добавить эту функциональность
"""

# Это пример интеграции - нужно добавить в generate_live_report.py

"""
ДОБАВИТЬ В generate_live_report.py:

from scores24_snapshot_enricher import (
    get_scores24_snapshot_data,
    extract_minutes_from_snapshot,
    extract_tennis_sets_from_snapshot,
    enrich_match_with_snapshot
)

def _enrich_matches_with_snapshot(
    matches: List[Dict],
    sport: str,
    mcp_browser_navigate=None,
    mcp_browser_wait=None,
    mcp_browser_snapshot=None
) -> List[Dict]:
    '''
    Обогащает матчи данными из snapshot (минуты, сеты)
    Используется только если данных не хватает в GraphQL
    '''
    if not matches:
        return matches
    
    # Проверяем, нужен ли snapshot
    needs_minutes = any(m.get("minute_numeric") is None for m in matches)
    needs_sets = sport == "tennis" and any(not m.get("completed_sets") for m in matches)
    
    if not (needs_minutes or needs_sets):
        return matches  # Все данные есть в GraphQL
    
    # Проверяем наличие MCP Browser функций
    if not all([mcp_browser_navigate, mcp_browser_wait, mcp_browser_snapshot]):
        # Без MCP Browser не можем обогатить - возвращаем как есть
        return matches
    
    try:
        # Получаем snapshot (один раз для всех матчей)
        snapshot = get_scores24_snapshot_data(
            sport,
            mcp_browser_navigate,
            mcp_browser_wait,
            mcp_browser_snapshot
        )
        
        if not snapshot:
            return matches
        
        # Извлекаем данные из snapshot
        minutes = extract_minutes_from_snapshot(snapshot, sport)
        sets = None
        if sport == "tennis":
            sets = extract_tennis_sets_from_snapshot(snapshot)
        
        # Обогащаем каждый матч
        enriched = []
        for match in matches:
            enriched_match = enrich_match_with_snapshot(match, minutes, sets)
            enriched.append(enriched_match)
        
        return enriched
        
    except Exception as e:
        print(f"⚠️ Ошибка обогащения через snapshot: {e}")
        return matches  # В случае ошибки возвращаем исходные данные


# ИЗМЕНИТЬ В _select_top_matches:

def _select_top_matches(limit: int = 3, mcp_browser_navigate=None, mcp_browser_wait=None, mcp_browser_snapshot=None) -> List[Dict]:
    matches = analyze_live_matches(limit=120)
    
    # ОБОГАЩАЕМ ДАННЫЕ ЧЕРЕЗ SNAPSHOT
    matches = _enrich_matches_with_snapshot(
        matches,
        "soccer",
        mcp_browser_navigate,
        mcp_browser_wait,
        mcp_browser_snapshot
    )
    
    # Дальше как обычно...
    filtered: List[Dict] = []
    # ... остальной код


# ИЗМЕНИТЬ В _select_top_handball_matches:

def _select_top_handball_matches(limit: int = 2, mcp_browser_navigate=None, mcp_browser_wait=None, mcp_browser_snapshot=None) -> List[Dict]:
    if limit <= 0:
        return []
    
    matches = analyze_live_handball_matches(limit=80)
    
    # ОБОГАЩАЕМ ДАННЫЕ ЧЕРЕЗ SNAPSHOT (особенно важно для гандбола!)
    matches = _enrich_matches_with_snapshot(
        matches,
        "handball",
        mcp_browser_navigate,
        mcp_browser_wait,
        mcp_browser_snapshot
    )
    
    # Дальше как обычно...
    filtered: List[Dict] = []
    # ... остальной код


# ИЗМЕНИТЬ В _select_top_tennis_matches:

def _select_top_tennis_matches(limit: int = 2, mcp_browser_navigate=None, mcp_browser_wait=None, mcp_browser_snapshot=None) -> List[Dict]:
    if limit <= 0:
        return []
    
    matches = analyze_live_tennis_matches(limit=80)
    
    # ОБОГАЩАЕМ ДАННЫЕ ЧЕРЕЗ SNAPSHOT (для завершенных сетов)
    matches = _enrich_matches_with_snapshot(
        matches,
        "tennis",
        mcp_browser_navigate,
        mcp_browser_wait,
        mcp_browser_snapshot
    )
    
    # Дальше как обычно...
    filtered: List[Dict] = []
    # ... остальной код


# ИЗМЕНИТЬ В generate_live_report:

def generate_live_report(
    max_matches: int = 3,
    mcp_browser_navigate=None,
    mcp_browser_wait=None,
    mcp_browser_snapshot=None
) -> Tuple[str, List[Dict], Dict[str, Any]]:
    # ...
    
    football_matches = _select_top_matches(
        limit=max_matches,
        mcp_browser_navigate=mcp_browser_navigate,
        mcp_browser_wait=mcp_browser_wait,
        mcp_browser_snapshot=mcp_browser_snapshot
    )
    
    tennis_matches = _select_top_tennis_matches(
        limit=tennis_limit,
        mcp_browser_navigate=mcp_browser_navigate,
        mcp_browser_wait=mcp_browser_wait,
        mcp_browser_snapshot=mcp_browser_snapshot
    )
    
    handball_matches = _select_top_handball_matches(
        limit=handball_limit,
        mcp_browser_navigate=mcp_browser_navigate,
        mcp_browser_wait=mcp_browser_wait,
        mcp_browser_snapshot=mcp_browser_snapshot
    )
    
    # ...
"""

print("=" * 60)
print("ИНСТРУКЦИЯ ПО ИНТЕГРАЦИИ")
print("=" * 60)
print("\nСм. содержимое файла для деталей интеграции")
print("\nОСНОВНЫЕ ИЗМЕНЕНИЯ:")
print("1. Добавить импорт scores24_snapshot_enricher")
print("2. Добавить функцию _enrich_matches_with_snapshot")
print("3. Вызывать обогащение в _select_top_* функциях")
print("4. Передавать MCP Browser функции через generate_live_report")

