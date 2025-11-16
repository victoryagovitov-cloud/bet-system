#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Обогащение данных матчей через Browser MCP snapshot Scores24
Получает минуты и завершенные сеты, которых нет в GraphQL
"""

from typing import Dict, List, Optional, Any
import re


def extract_minutes_from_snapshot(snapshot_data: Dict[str, Any], sport: str = "soccer") -> Dict[str, Optional[int]]:
    """
    Извлекает минуты матчей из snapshot страницы Scores24
    
    Args:
        snapshot_data: данные snapshot от Browser MCP (YAML структура)
        sport: вид спорта (soccer, handball, tennis)
    
    Returns:
        Dict[slug, minute] - словарь slug матча -> минута
    """
    minutes_map = {}
    
    if not snapshot_data:
        return minutes_map
    
    # Структура snapshot: элементы с link содержат URL матча
    # Рядом с матчем есть текст с временем: "1-й т.", "2-й т.", "Перерыв"
    
    def _extract_slug_from_url(url: str) -> Optional[str]:
        """Извлекает slug из URL вида /ru/handball/m-12-11-2025-kolstad-handball-veszprem"""
        if not url or not isinstance(url, str):
            return None
        # Паттерн: /ru/{sport}/m-{date}-{slug}
        match = re.search(r"/ru/(?:handball|soccer|tennis)/m-\d+-\d+-\d+-(.+)", url)
        if match:
            return match.group(1)
        return None
    
    def _parse_minute_from_text(text: str, sport: str) -> Optional[int]:
        """Парсит минуту из текста"""
        if not text or not isinstance(text, str):
            return None
        
        text_lower = text.lower()
        
        # Гандбол: сначала ищем конкретные минуты (например, "37'"), потом периоды
        if sport == "handball":
            # Сначала ищем конкретную минуту (например, "37'", "43 мин")
            minute_match = re.search(r"(\d+)\s*['\"]", text)
            if minute_match:
                minute = int(minute_match.group(1))
                # В гандболе матч длится 60 минут (2 тайма по 30)
                if 1 <= minute <= 60:
                    return minute
            # Если конкретной минуты нет, проверяем периоды
            if "перерыв" in text_lower:
                return 30
            elif "1-й т." in text_lower or "1-й тайм" in text_lower:
                # Первый тайм - примерно 15-25 минут (берем среднее 20)
                return 20
            elif "2-й т." in text_lower or "2-й тайм" in text_lower:
                # Второй тайм - примерно 35-50 минут (берем среднее 42)
                return 42
        
        # Футбол: "45'", "HT", "FT"
        if sport == "soccer":
            # Ищем паттерны минут
            minute_match = re.search(r"(\d+)\s*['\"]", text)
            if minute_match:
                return int(minute_match.group(1))
            if "ht" in text_lower or "перерыв" in text_lower:
                return 45
            if "ft" in text_lower:
                return 90
        
        return None
    
    def _parse_snapshot_recursive(node: Any, context: Dict[str, Any] = None):
        """Рекурсивно парсим snapshot для поиска минут"""
        if context is None:
            context = {"current_slug": None, "recent_texts": [], "pending_minute": None}
        
        if isinstance(node, dict):
            # Проверяем link с URL матча
            if "/url" in node:
                url = node.get("/url", "")
                slug = _extract_slug_from_url(url)
                if slug:
                    # Если есть ожидающая минута, связываем её с этим slug
                    if context["pending_minute"] is not None:
                        minutes_map[slug] = context["pending_minute"]
                        context["pending_minute"] = None
                    context["current_slug"] = slug
                    # Также проверяем недавние тексты
                    for text in context["recent_texts"][-3:]:
                        minute = _parse_minute_from_text(text, sport)
                        if minute is not None:
                            minutes_map[slug] = minute
                            break
            
            # Проверяем текст на наличие минуты
            text = node.get("text", "")
            if text:
                # Сохраняем текст в контекст
                context["recent_texts"].append(text)
                if len(context["recent_texts"]) > 5:
                    context["recent_texts"].pop(0)
                
                # Парсим минуту из текста
                minute = _parse_minute_from_text(text, sport)
                if minute is not None:
                    # Если есть текущий slug, сразу связываем
                    if context["current_slug"]:
                        minutes_map[context["current_slug"]] = minute
                    else:
                        # Сохраняем для следующего URL
                        context["pending_minute"] = minute
            
            # Рекурсивно обрабатываем дочерние элементы
            for key, value in node.items():
                if key not in ["text", "ref", "/url"]:
                    _parse_snapshot_recursive(value, context)
        
        elif isinstance(node, list):
            for item in node:
                _parse_snapshot_recursive(item, context)
    
    # Парсим snapshot
    _parse_snapshot_recursive(snapshot_data)
    
    return minutes_map


def extract_tennis_sets_from_snapshot(snapshot_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Извлекает завершенные сеты из snapshot для тенниса
    
    Args:
        snapshot_data: данные snapshot от Browser MCP
    
    Returns:
        Dict[slug, sets] - словарь slug матча -> список завершенных сетов
        Формат sets: [{"set": 1, "home": 6, "away": 4}, ...]
    """
    sets_map = {}
    
    if not snapshot_data:
        return sets_map
    
    def _parse_snapshot_recursive(node: Any, current_match: Optional[str] = None):
        """Рекурсивно парсим snapshot для поиска сетов"""
        if isinstance(node, dict):
            text = node.get("text", "")
            
            # Ищем паттерны сетов: "6:4", "6:2 6:3", "6:4 3:6 6:2"
            # Формат: два числа через двоеточие
            set_pattern = r"(\d+):(\d+)"
            sets_found = re.findall(set_pattern, text)
            
            if sets_found and current_match:
                sets_list = []
                for i, (home, away) in enumerate(sets_found, 1):
                    try:
                        sets_list.append({
                            "set": i,
                            "home": int(home),
                            "away": int(away)
                        })
                    except:
                        pass
                
                if sets_list:
                    sets_map[current_match] = sets_list
            
            # Рекурсивно обрабатываем дочерние элементы
            for key, value in node.items():
                if key not in ["text", "ref"]:
                    _parse_snapshot_recursive(value, current_match)
        
        elif isinstance(node, list):
            for item in node:
                _parse_snapshot_recursive(item, current_match)
    
    # Парсим snapshot
    _parse_snapshot_recursive(snapshot_data)
    
    return sets_map


def enrich_match_with_snapshot(
    match: Dict[str, Any],
    snapshot_minutes: Dict[str, Optional[int]],
    snapshot_sets: Optional[Dict[str, List[Dict[str, Any]]]] = None
) -> Dict[str, Any]:
    """
    Обогащает данные матча информацией из snapshot
    
    Args:
        match: данные матча из GraphQL
        snapshot_minutes: словарь slug -> минута из snapshot
        snapshot_sets: словарь slug -> сеты для тенниса (опционально)
    
    Returns:
        Обогащенный матч
    """
    slug = match.get("slug")
    if not slug:
        return match
    
    # Пытаемся найти минуту в snapshot по slug
    # Slug может быть в разных форматах, пробуем разные варианты
    minute = None
    
    # Прямое совпадение
    if slug in snapshot_minutes:
        minute = snapshot_minutes[slug]
    else:
        # Пробуем найти по частичному совпадению (slug может отличаться)
        slug_parts = slug.split("-")
        for snapshot_slug, snapshot_minute in snapshot_minutes.items():
            # Проверяем, есть ли общие части в slug
            snapshot_parts = snapshot_slug.split("-")
            # Если хотя бы 2 части совпадают - считаем это одним матчем
            common_parts = set(slug_parts) & set(snapshot_parts)
            if len(common_parts) >= 2:
                minute = snapshot_minute
                break
    
    # Добавляем минуту из snapshot, если её нет в GraphQL
    if match.get("minute_numeric") is None and minute is not None:
        match["minute_numeric"] = minute
        match["minute"] = str(minute)
        match["minute_source"] = "snapshot"
    
    # Для тенниса добавляем завершенные сеты
    if snapshot_sets:
        sets = None
        if slug in snapshot_sets:
            sets = snapshot_sets[slug]
        else:
            # Пробуем найти по частичному совпадению
            slug_parts = slug.split("-")
            for snapshot_slug, snapshot_sets_data in snapshot_sets.items():
                snapshot_parts = snapshot_slug.split("-")
                common_parts = set(slug_parts) & set(snapshot_parts)
                if len(common_parts) >= 2:
                    sets = snapshot_sets_data
                    break
        
        if sets:
            match["completed_sets"] = sets
            match["sets_source"] = "snapshot"
    
    return match


def get_scores24_snapshot_data(
    sport: str,
    mcp_browser_navigate,
    mcp_browser_wait,
    mcp_browser_snapshot
) -> Dict[str, Any]:
    """
    Получает snapshot страницы Scores24 для вида спорта
    
    Args:
        sport: вид спорта (soccer, handball, tennis)
        mcp_browser_navigate: функция Browser MCP для навигации
        mcp_browser_wait: функция Browser MCP для ожидания
        mcp_browser_snapshot: функция Browser MCP для snapshot
    
    Returns:
        Данные snapshot
    """
    urls = {
        "soccer": "https://scores24.live/ru/soccer?matchesFilter=live",
        "handball": "https://scores24.live/ru/handball?matchesFilter=live",
        "tennis": "https://scores24.live/ru/tennis?matchesFilter=live",
    }
    
    url = urls.get(sport, urls["soccer"])
    
    try:
        mcp_browser_navigate(url)
        mcp_browser_wait(time=5)
        snapshot = mcp_browser_snapshot()
        return snapshot
    except Exception as e:
        print(f"⚠️ Ошибка получения snapshot для {sport}: {e}")
        return {}


# Пример использования (для тестирования)
if __name__ == "__main__":
    print("Этот модуль должен использоваться с Browser MCP функциями из Cursor")
    print("Пример использования:")
    print("""
    from scores24_snapshot_enricher import (
        get_scores24_snapshot_data,
        extract_minutes_from_snapshot,
        enrich_match_with_snapshot
    )
    
    # В контексте Cursor с MCP Browser:
    snapshot = get_scores24_snapshot_data(
        "soccer",
        mcp_browser_navigate,
        mcp_browser_wait,
        mcp_browser_snapshot
    )
    
    minutes = extract_minutes_from_snapshot(snapshot, "soccer")
    
    # Обогащаем матчи
    for match in matches:
        match = enrich_match_with_snapshot(match, minutes)
    """)

