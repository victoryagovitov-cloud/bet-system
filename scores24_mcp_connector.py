# -*- coding: utf-8 -*-
"""
🌐 ПРОВЕРКА SCORES24 ЧЕРЕЗ MCP BROWSER
Использует MCP Browser вместо Selenium (который блокируется)
"""
import re
import time

def get_name_variants(name):
    """Генерация вариантов названий для поиска"""
    variants = set()
    
    # Базовый вариант
    name_clean = name.strip().lower()
    variants.add(name_clean)
    
    # Без скобок
    no_brackets = re.sub(r'\([^)]*\)', '', name).strip().lower()
    if no_brackets:
        variants.add(no_brackets)
    
    # Для составных имён
    if '/' in name:
        parts = name.split('/')
        for part in parts:
            variants.add(part.strip().lower())
    
    # Без инициалов
    if '.' in name:
        without_dot = name.split('.')[0].strip().lower()
        variants.add(without_dot)
    
    # Отдельные слова
    words = name.split()
    for word in words:
        clean_word = word.strip().lower()
        if len(clean_word) > 2:  # Игнорируем короткие слова типа "А", "ФК"
            variants.add(clean_word)
    
    # Последние 2 слова (для длинных названий)
    if len(words) >= 2:
        last_two = ' '.join(words[-2:]).lower()
        variants.add(last_two)
    
    return list(variants)

def parse_match_stats_from_snapshot(snapshot_text):
    """
    Парсит статистику матча из snapshot Scores24
    
    Ищет:
    - xG (Expected Goals)
    - Владение мячом (Possession)
    - Удары (Shots)
    - Удары в створ (Shots on target)
    """
    stats = {
        'xG': {'team1': None, 'team2': None},
        'possession': {'team1': None, 'team2': None},
        'shots': {'team1': None, 'team2': None},
        'shots_on_target': {'team1': None, 'team2': None}
    }
    
    snapshot_lower = snapshot_text.lower()
    
    # Поиск xG
    xg_pattern = r'xG[^0-9]*?([\d.]+)[^0-9]*?([\d.]+)'
    xg_match = re.search(xg_pattern, snapshot_text, re.IGNORECASE)
    if xg_match:
        try:
            stats['xG']['team1'] = float(xg_match.group(1))
            stats['xG']['team2'] = float(xg_match.group(2))
        except:
            pass
    
    # Поиск владения (может быть в разных форматах)
    possession_patterns = [
        r'владение[^0-9]*?(\d+)%[^0-9]*?(\d+)%',
        r'possession[^0-9]*?(\d+)%[^0-9]*?(\d+)%',
        r'(\d+)%[^0-9]*?владение[^0-9]*?(\d+)%'
    ]
    for pattern in possession_patterns:
        poss_match = re.search(pattern, snapshot_text, re.IGNORECASE)
        if poss_match:
            try:
                stats['possession']['team1'] = int(poss_match.group(1))
                stats['possession']['team2'] = int(poss_match.group(2))
                break
            except:
                pass
    
    # Поиск ударов
    shots_pattern = r'удары[^0-9]*?(\d+)[^0-9]*?(\d+)'
    shots_match = re.search(shots_pattern, snapshot_text, re.IGNORECASE)
    if shots_match:
        try:
            stats['shots']['team1'] = int(shots_match.group(1))
            stats['shots']['team2'] = int(shots_match.group(2))
        except:
            pass

    # Поиск ударов в створ
    shots_on_target_patterns = [
        r'в створ[^0-9]*?(\d+)[^0-9]*?(\d+)',
        r'shots on target[^0-9]*?(\d+)[^0-9]*?(\d+)'
    ]
    for pattern in shots_on_target_patterns:
        sot_match = re.search(pattern, snapshot_text, re.IGNORECASE)
        if sot_match:
            try:
                stats['shots_on_target']['team1'] = int(sot_match.group(1))
                stats['shots_on_target']['team2'] = int(sot_match.group(2))
                break
            except:
                pass
    
    return stats

def check_scores24_mcp(sport, team1, team2, match_data):
    """
    Проверка матча на Scores24 через MCP Browser
    
    Args:
        sport: 'football', 'tennis', 'handball'
        team1: название первой команды/игрока
        team2: название второй команды/игрока
        match_data: словарь с данными матча
    
    Returns:
        dict с результатами проверки
    """
    print(f"🔍 Проверяю через MCP Browser: {team1} - {team2}")
    print(f"   Спорт: {sport}")
    
    urls = {
        'football': 'https://scores24.live/ru/soccer?matchesFilter=live',
        'tennis': 'https://scores24.live/ru/tennis?matchesFilter=live',
        'handball': 'https://scores24.live/ru/handball?matchesFilter=live'
    }
    
    try:
        # ШАГ 1: Открыть список live-матчей
        url = urls[sport]
        print(f"   📡 Открываю: {url}")
        
        # ВАЖНО: Эта функция должна вызываться из контекста, где доступны MCP Browser функции
        # Здесь мы только описываем логику, реальный вызов будет в основном скрипте
        
        # Генерируем варианты названий
        team1_variants = get_name_variants(team1)
        team2_variants = get_name_variants(team2)
        
        print(f"   🔍 Варианты команды 1 ({len(team1_variants)}): {team1_variants[:5]}")
        print(f"   🔍 Варианты команды 2 ({len(team2_variants)}): {team2_variants[:5]}")
        
        # Возвращаем структуру для дальнейшей обработки через MCP
        return {
            'sport': sport,
            'team1': team1,
            'team2': team2,
            'team1_variants': team1_variants,
            'team2_variants': team2_variants,
            'match_data': match_data,
            'url': url
        }
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return {'verified': False, 'error': str(e)}

def verify_match_in_snapshot(snapshot_text, team1_variants, team2_variants):
    """
    Проверяет наличие матча в snapshot по вариантам названий
    
    Returns:
        tuple: (found, found_variants_team1, found_variants_team2)
    """
    snapshot_lower = snapshot_text.lower()
    
    found_variants_1 = [v for v in team1_variants if v in snapshot_lower]
    found_variants_2 = [v for v in team2_variants if v in snapshot_lower]
    
    found = len(found_variants_1) > 0 and len(found_variants_2) > 0
    
    return found, found_variants_1, found_variants_2

def format_stats_details(stats):
    """Форматирует статистику для сообщения"""
    details_parts = []
    
    if stats['xG']['team1'] is not None and stats['xG']['team2'] is not None:
        details_parts.append(f"xG {stats['xG']['team1']:.2f}-{stats['xG']['team2']:.2f}")
    
    if stats['possession']['team1'] is not None and stats['possession']['team2'] is not None:
        details_parts.append(f"владение {stats['possession']['team1']}%-{stats['possession']['team2']}%")
    
    if stats['shots']['team1'] is not None and stats['shots']['team2'] is not None:
        details_parts.append(f"удары {stats['shots']['team1']}-{stats['shots']['team2']}")
    
    if stats['shots_on_target']['team1'] is not None and stats['shots_on_target']['team2'] is not None:
        details_parts.append(f"в створ {stats['shots_on_target']['team1']}-{stats['shots_on_target']['team2']}")
    
    return ", ".join(details_parts)

