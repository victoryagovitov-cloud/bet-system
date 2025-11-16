# -*- coding: utf-8 -*-
"""
🌐 ПРОВЕРКА SCORES24 ЧЕРЕЗ MCP BROWSER
Полная реализация с использованием MCP Browser инструментов
"""
import re
import time
from scores24_mcp_connector import (
    get_name_variants,
    verify_match_in_snapshot,
    parse_match_stats_from_snapshot,
    format_stats_details
)

def check_match_on_scores24_mcp(
    sport,
    team1,
    team2,
    match_data,
    mcp_browser_navigate,
    mcp_browser_wait,
    mcp_browser_snapshot,
    live_snapshot_text=None
):
    """
    Проверяет матч на Scores24 через MCP Browser
    
    Args:
        sport: 'football', 'tennis', 'handball'
        team1: название первой команды/игрока
        team2: название второй команды/игрока
        match_data: словарь с данными матча
        mcp_browser_navigate: функция MCP Browser для навигации
        mcp_browser_wait: функция MCP Browser для ожидания
        mcp_browser_snapshot: функция MCP Browser для получения snapshot
    
    Returns:
        dict с результатами проверки
    """
    print(f"🔍 Проверяю через MCP Browser: {team1} - {team2}")
    print(f"   Спорт: {sport}")
    
    try:
        snapshot_text = live_snapshot_text
        match_page_url = match_data.get('scores24_url')
        
        if snapshot_text is None and not match_page_url:
            urls = {
                'football': 'https://scores24.live/ru/soccer?matchesFilter=live',
                'tennis': 'https://scores24.live/ru/tennis?matchesFilter=live',
                'handball': 'https://scores24.live/ru/handball?matchesFilter=live'
            }
            url = urls[sport]
            print(f"   📡 Открываю: {url}")
            
            mcp_browser_navigate(url)
            mcp_browser_wait(time=5)
            
            snapshot_result = mcp_browser_snapshot()
            snapshot_text = snapshot_result.get('snapshot', '') if isinstance(snapshot_result, dict) else str(snapshot_result)
        
        # Генерируем варианты названий
        team1_variants = get_name_variants(team1)
        team2_variants = get_name_variants(team2)
        
        print(f"   🔍 Варианты команды 1 ({len(team1_variants)}): {team1_variants[:3]}")
        print(f"   🔍 Варианты команды 2 ({len(team2_variants)}): {team2_variants[:3]}")
        
        found_variants_1 = []
        found_variants_2 = []
        
        if not match_page_url:
            # Проверяем наличие матча в списке
            found, found_variants_1, found_variants_2 = verify_match_in_snapshot(
                snapshot_text, team1_variants, team2_variants
            )
            
            if not found:
                print(f"   ❌ Матч не найден в списке live-матчей")
                return {'verified': False}
            
            print(f"   ✅ Матч найден в списке!")
            print(f"      Найдено команды 1: {found_variants_1[:2]}")
            print(f"      Найдено команды 2: {found_variants_2[:2]}")
            
            # ШАГ 2: Ищем ссылку на страницу матча в snapshot
            match_url_pattern = r'/ru/(?:soccer|tennis|handball)/m-[^"\s]+'
            import re
            match_links = re.findall(match_url_pattern, snapshot_text)
            
            for link in match_links:
                link_lower = link.lower()
                if any(v in link_lower for v in team1_variants[:3]) and any(v in link_lower for v in team2_variants[:3]):
                    match_page_url = f"https://scores24.live{link}"
                    break
            
            if match_page_url:
                match_data['scores24_url'] = match_page_url
        
        stats_details = "Матч найден на Scores24"
        stats = {}
        
        if not match_page_url:
            print("   ❌ Не удалось определить ссылку на страницу матча")
            return {'verified': False}
        
        print(f"   📊 Открываю страницу матча: {match_page_url}")
        try:
            mcp_browser_navigate(match_page_url)
            mcp_browser_wait(time=5)
            
            match_snapshot_text = _take_snapshot_text(mcp_browser_snapshot)
            stats, stats_details = _collect_stats_with_retry(
                match_snapshot_text,
                lambda: _take_snapshot_text(mcp_browser_snapshot),
                team1,
                team2
            )

            if not stats_details:
                print("   ❌ На странице матча отсутствует live-статистика — пропускаем")
                return {'verified': False, 'reason': 'no_stats'}
            
            print(f"   ✅ Статистика собрана: {stats_details}")
        except Exception as e:
            print(f"   ⚠️ Не удалось собрать детальную статистику: {e}")
            return {'verified': False, 'reason': 'error_collecting_stats', 'error': str(e)}
        
        return {
            'verified': True,
            'source': 'Scores24.live (MCP Browser)',
            'details': stats_details,
            'match': match_data,
            'stats': stats,
            'found_variants': found_variants_1 + found_variants_2
        }
        
    except Exception as e:
        print(f"   ❌ Ошибка при проверке: {e}")
        import traceback
        traceback.print_exc()
        return {'verified': False, 'error': str(e)}


def _normalize(text: str) -> str:
    return re.sub(r'[^a-zа-я0-9]+', ' ', text.lower()).strip()


def _extract_table_positions(snapshot_text: str, team1: str, team2: str) -> str:
    """
    Пытается найти позиции команд в таблице по тексту snapshot.
    Возвращает строку вида «позиции: 10-е против 8-го».
    """
    if not snapshot_text:
        return ""

    lines = snapshot_text.splitlines()
    team_positions = {}
    search_names = {
        'team1': _normalize(team1),
        'team2': _normalize(team2)
    }

    for line in lines:
        norm_line = _normalize(line)
        if not norm_line:
            continue

        pos_match = re.search(r'(\d+)\s*\.', line)
        if not pos_match:
            continue

        position = pos_match.group(1)
        for key, name in search_names.items():
            if name and name in norm_line and key not in team_positions:
                team_positions[key] = position

        if len(team_positions) == 2:
            break

    if not team_positions:
        return ""

    team1_pos = team_positions.get('team1')
    team2_pos = team_positions.get('team2')

    parts = []
    if team1_pos:
        parts.append(f"{team1_pos}-е место")
    if team2_pos:
        parts.append(f"{team2_pos}-е у соперника")

    return f"позиции: {' vs '.join(parts)}" if parts else ""


def _take_snapshot_text(snapshot_callable) -> str:
    snapshot_result = snapshot_callable()
    return snapshot_result.get('snapshot', '') if isinstance(snapshot_result, dict) else str(snapshot_result)


def _has_stats(stats: dict) -> bool:
    if not stats:
        return False
    keys = ('xG', 'possession', 'shots', 'shots_on_target')
    for key in keys:
        block = stats.get(key, {})
        if isinstance(block, dict):
            if block.get('team1') is not None or block.get('team2') is not None:
                return True
    return False


def _collect_stats_with_retry(initial_text, retry_snapshot_callable, team1, team2):
    """
    Возвращает (stats, stats_details), при необходимости делая повторный снимок.
    """
    stats = parse_match_stats_from_snapshot(initial_text)
    stats_details = format_stats_details(stats)

    positions_note = _extract_table_positions(initial_text, team1, team2)
    if positions_note:
        stats_details = f"{stats_details}; {positions_note}" if stats_details else positions_note

    if stats_details and _has_stats(stats):
        return stats, stats_details

    print("   ⚠️ Статистика пустая, повторяю snapshot (ожидание 2 секунды)")
    stats = {}
    stats_details = ""
    time.sleep(2)

    next_text = retry_snapshot_callable()
    stats = parse_match_stats_from_snapshot(next_text)
    stats_details = format_stats_details(stats)

    positions_note = _extract_table_positions(next_text, team1, team2)
    if positions_note:
        stats_details = f"{stats_details}; {positions_note}" if stats_details else positions_note

    return stats, stats_details

