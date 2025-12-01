from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import sys
import math
import re
import random
_DIGRAPH_MAP = {
    "sh": "ш",
    "ch": "ч",
    "sch": "щ",
    "zh": "ж",
    "kh": "х",
    "ph": "ф",
    "th": "т",
    "ts": "ц",
    "ya": "я",
    "yu": "ю",
    "yo": "ё",
    "ye": "е",
}

_CHAR_MAP = {
    "a": "а",
    "b": "б",
    "c": "к",
    "d": "д",
    "e": "е",
    "f": "ф",
    "g": "г",
    "h": "х",
    "i": "и",
    "j": "дж",
    "k": "к",
    "l": "л",
    "m": "м",
    "n": "н",
    "o": "о",
    "p": "п",
    "q": "к",
    "r": "р",
    "s": "с",
    "t": "т",
    "u": "у",
    "v": "в",
    "w": "в",
    "x": "кс",
    "y": "и",
    "z": "з",
}


def _transliterate_token(token: str) -> str:
    lower = token.lower()
    output: List[str] = []
    i = 0
    while i < len(lower):
        matched = False
        for diag, repl in sorted(_DIGRAPH_MAP.items(), key=lambda x: -len(x[0])):
            if lower.startswith(diag, i):
                output.append(repl)
                i += len(diag)
                matched = True
                break
        if matched:
            continue
        ch = lower[i]
        repl = _CHAR_MAP.get(ch)
        if repl is None:
            output.append(token[i])
        else:
            output.append(repl)
        i += 1

    combined = "".join(output)
    if token.isupper():
        return combined.upper()
    if token and token[0].isupper():
        return combined.capitalize()
    return combined


def _transliterate_name(name: str) -> str:
    def repl(match: re.Match[str]) -> str:
        word = match.group(0)
        return _transliterate_token(word)

    return re.sub(r"[A-Za-z]+", repl, name)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from graphql_live_analyzer import analyze_live_matches
from graphql_tennis_analyzer import analyze_live_tennis_matches
from graphql_basketball_analyzer import analyze_live_basketball_matches
from graphql_volleyball_analyzer import analyze_live_volleyball_matches
from graphql_american_football_analyzer import analyze_live_american_football_matches
from graphql_dota2_analyzer import analyze_live_dota2_matches
from league_filter import should_include_match, get_league_tier
from optimized_filters import (
    apply_odds_correction,
    check_safe_match_criteria,
    check_risky_match_criteria,
    SAFE_FILTERS,
    RISKY_FILTERS,
    PRIMARY_FILTERS
)

# Новые модули системы
try:
    from system_logger import get_logger, log_info, log_warning, log_error, log_debug
    from system_config import get_config
    from data_validator import get_validator, validate_match, sanitize_match
    SYSTEM_MODULES_AVAILABLE = True
except ImportError:
    SYSTEM_MODULES_AVAILABLE = False
    # Fallback функции для совместимости
    def get_logger():
        import logging
        return logging.getLogger("system")
    def log_info(msg, **kwargs):
        print(f"INFO: {msg}")
    def log_warning(msg, **kwargs):
        print(f"WARNING: {msg}")
    def log_error(msg, **kwargs):
        print(f"ERROR: {msg}")
    def log_debug(msg, **kwargs):
        print(f"DEBUG: {msg}")
    def get_config():
        return None
    def get_validator():
        return None
    def validate_match(match):
        return True, []
    def sanitize_match(match):
        return match

try:
    from football_data_org_client import enrich_match_with_league_data
    FOOTBALL_DATA_ORG_AVAILABLE = True
except ImportError:
    FOOTBALL_DATA_ORG_AVAILABLE = False
from team_history_analyzer import adjust_probability_with_history
from scores24_graphql_client import fetch_match_odds
from strength_integration import enrich_match_with_strength, get_strength_based_probability
from pathlib import Path
import csv

try:
    from tuning_settings import SETTINGS as TUNING_SETTINGS
except ImportError:
    @dataclass(frozen=True)
    class _DefaultSettings:
        max_matches: int = 5
        filter_relaxation: float = 1.0
        enable_secondary_dedup: bool = True
        probability_floor: float = 0.55
        probability_cap: float = 0.92
        basketball_probability_floor: float = 0.60
        basketball_probability_cap: float = 0.90
        basketball_filter_relaxation: float = 1.0
        football_probability_floor: float = 0.65  # 65% - нижняя граница для футбола
        football_probability_cap: float = 0.90  # 90% - верхняя граница для футбола
        tennis_probability_floor: float = 0.70
        tennis_probability_cap: float = 0.92
        filter_repeat_matches: bool = True  # По умолчанию фильтруем повторные матчи

    TUNING_SETTINGS = _DefaultSettings()

# Импорт обогащения через snapshot (опционально, если MCP Browser доступен)
try:
    from scores24_snapshot_enricher import (
        get_scores24_snapshot_data,
        extract_minutes_from_snapshot,
        extract_tennis_sets_from_snapshot,
        enrich_match_with_snapshot
    )
    SNAPSHOT_ENRICHMENT_AVAILABLE = True
except ImportError:
    SNAPSHOT_ENRICHMENT_AVAILABLE = False


@dataclass
class OddsInfo:
    value: Optional[float]
    bookmaker: Optional[str]


# КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: Фокус на коэффициенты 1.15-1.30 (ПОСЛЕ коррекции)
# Коэффициенты Scores24 завышены на ~13-15%, поэтому:
# - 1.15 после коррекции = ~1.32 на Scores24 (при коррекции 13%)
# - 1.30 после коррекции = ~1.50 на Scores24 (при коррекции 13%)
# Минимальный коэффициент ПОСЛЕ коррекции: 1.15 (для ROI > 5%)
MIN_ODDS_CORRECTED = 1.12  # Минимальный коэффициент ПОСЛЕ коррекции (ослаблено с 1.15)
MIN_ODDS_SOURCE = 1.29  # Минимальный коэффициент на Scores24 (до коррекции, при коррекции 13%)

# Максимальный коэффициент ПОСЛЕ коррекции: 1.35 (увеличено с 1.30 для большего количества матчей)
MAX_ODDS_CORRECTED = 1.35  # Максимальный коэффициент ПОСЛЕ коррекции (ослаблено с 1.30)
MAX_ODDS_SOURCE = 1.55  # Максимальный коэффициент на Scores24 (до коррекции, при коррекции 13%)

# Старые константы оставляем для совместимости, но они больше не используются для фильтрации
_BASE_PRIMARY_MAX_ODDS = 1.10  # DEPRECATED: используем MIN_ODDS_CORRECTED и MAX_ODDS_CORRECTED
_BASE_EXTENDED_MAX_ODDS = 1.50  # DEPRECATED
_BASE_EXTENDED_MIN_DOMINANCE = 6.0
_BASE_EXTENDED_MIN_XG_DIFF = 0.3
_BASE_EXTENDED_MIN_SOT_DIFF = 1.0
_BASE_PREFERRED_MIN_ODDS = 1.15

RELAX_FACTOR = max(0.5, min(1.5, TUNING_SETTINGS.filter_relaxation))
RELAX_DELTA = max(0.0, min(1.0, 1.0 - RELAX_FACTOR))

PRIMARY_MAX_ODDS = _BASE_PRIMARY_MAX_ODDS + 0.5 * RELAX_DELTA
EXTENDED_MAX_ODDS = _BASE_EXTENDED_MAX_ODDS + 0.8 * RELAX_DELTA
# Ужесточенные требования для EXTENDED tier - баланс между количеством и качеством
EXTENDED_MIN_DOMINANCE = _BASE_EXTENDED_MIN_DOMINANCE * RELAX_FACTOR
EXTENDED_MIN_XG_DIFF = _BASE_EXTENDED_MIN_XG_DIFF * RELAX_FACTOR
EXTENDED_MIN_SOT_DIFF = max(0.0, _BASE_EXTENDED_MIN_SOT_DIFF * RELAX_FACTOR)
# Приоритизируем матчи с более высокими коэффициентами для поднятия среднего до 1.2
PREFERRED_MIN_ODDS = max(1.05, _BASE_PREFERRED_MIN_ODDS - 0.3 * RELAX_DELTA)

PROBABILITY_MIN = int(round(getattr(TUNING_SETTINGS, "probability_floor", 0.55) * 100))
PROBABILITY_MAX = int(round(getattr(TUNING_SETTINGS, "probability_cap", 0.92) * 100))
if PROBABILITY_MIN >= PROBABILITY_MAX:
    PROBABILITY_MIN = min(PROBABILITY_MIN, 70)
    PROBABILITY_MAX = max(PROBABILITY_MAX, PROBABILITY_MIN + 5)


def _enrich_matches_with_snapshot(
    matches: List[Dict],
    sport: str,
    mcp_browser_navigate=None,
    mcp_browser_wait=None,
    mcp_browser_snapshot=None
) -> List[Dict]:
    """
    Обогащает матчи данными из snapshot (минуты, сеты)
    Используется только если данных не хватает в GraphQL
    """
    if not matches or not SNAPSHOT_ENRICHMENT_AVAILABLE:
        return matches
    
    # Проверяем, нужен ли snapshot
    needs_minutes = any(m.get("minute_numeric") is None for m in matches)
    needs_sets = sport == "tennis" and any(not m.get("completed_sets") for m in matches)
    
    if not (needs_minutes or needs_sets):
        return matches  # Все данные есть в GraphQL
    
    # Проверяем наличие MCP Browser функций
    if not all([mcp_browser_navigate, mcp_browser_wait, mcp_browser_snapshot]):
        return matches  # Без MCP Browser не можем обогатить
    
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
        # В случае ошибки возвращаем исходные данные
        return matches


def _select_top_matches(
    limit: int = 3
) -> List[Dict]:
    matches = analyze_live_matches(limit=120)
    
    filtered: List[Dict] = []
    for match in matches:
        # ФИЛЬТРАЦИЯ ПО ЛИГАМ
        tournament = match.get("tournament") or match.get("tournament_name", "")
        country = match.get("country") or (match.get("country", {}) if isinstance(match.get("country"), dict) else {}).get("name", "")
        if isinstance(country, dict):
            country = country.get("name", "")
        
        # Определяем уровень лиги для анализа
        league_tier = get_league_tier(tournament, country, "football")
        match["league_tier"] = league_tier
        
        # УЖЕСТОЧЕННАЯ ФИЛЬТРАЦИЯ: Топ лиги ИЛИ наличие xG
        # Матч проходит, если это топ лига ИЛИ есть данные xG
        is_top_league = should_include_match(tournament, country, "football", exclude_mid_leagues=True)
        has_xg = match.get("has_xg", False) and match.get("xg") and match["xg"][0] is not None and match["xg"][1] is not None
        
        # Исключаем матч только если НЕ топ лига И НЕТ xG
        if not is_top_league and not has_xg:
            log_debug(f"Filtered football match {match.get('slug', 'unknown')}: Not top league and no xG data")
            continue
        
        # ОБОГАЩАЕМ МАТЧ ИНФОРМАЦИЕЙ О СИЛЕ КОМАНД
        match = enrich_match_with_strength(match)
        
        # Анализируем все матчи с хоть каким-то перевесом (даже минимальным)
        dominance = match.get("dominance_score", 0)
        if dominance < -5.0:  # Только отфильтровываем явных аутсайдеров
            continue

        # Получаем коэффициенты (с мониторингом, если доступен)
        try:
            from monitor_odds_delay import monitor_odds_fetch
            match_minute = match.get("minute_numeric")
            odds = monitor_odds_fetch(
                match["slug"], 
                match["leader_index"], 
                sport="soccer",
                match_minute=match_minute,
                match=match
            )
        except ImportError:
            # Если модуль мониторинга недоступен, используем обычный метод
            # Передаем match для получения реальных коэффициентов с BetBoom
            odds = _get_leader_odds(match["slug"], match["leader_index"], sport="soccer", match=match)
        
        # Проверяем, что odds существует и value не None
        if odds is None or odds.value is None:
            continue
        
        # ПРИМЕНЯЕМ КОРРЕКЦИЮ КОЭФФИЦИЕНТОВ
        odds_corrected = apply_odds_correction(odds.value)
        match["odds_corrected"] = odds_corrected
        
        # НОВЫЙ ПОДХОД: НЕ фильтруем по коэффициентам - анализируем все матчи по статистике
        # Коэффициенты показываем как рекомендацию, а не как фильтр
        # Это позволяет находить больше матчей и давать подписчикам выбор

        # Получаем вероятность (от AI или оценку)
        probability = match.get("claude_probability") or match.get("estimated_probability") or 0.0
        
        # НОВЫЙ ПОДХОД: Проверяем только статистику, без фильтрации по коэффициентам
        # Проверяем критерии по статистике (dominance, xG, владение и т.д.)
        passed, reason = check_safe_match_criteria(match, odds_corrected, probability)
        if passed:
            # Матч прошел проверку по статистике - добавляем его
            odds_tier = "safe"
            match_category = "safe"
        else:
            # Не прошел safe, проверяем risky (более мягкие критерии)
            passed, reason = check_risky_match_criteria(match, odds_corrected, probability)
            if passed:
                odds_tier = "risky"
                match_category = "risky"
            else:
                continue  # Не прошел ни safe, ни risky критерии по статистике

        match["odds_info"] = odds
        match["odds_tier"] = odds_tier
        match["match_category"] = match_category
        match["sport"] = "football"
        match["sport_type"] = "football"
        # Транслитерируем названия команд
        names = match.get("teams") or []
        if names:
            match["teams"] = [_transliterate_name(name) for name in names]
        
        # ОБОГАЩАЕМ ДАННЫМИ ИЗ FOOTBALL-DATA.ORG (если доступно)
        if FOOTBALL_DATA_ORG_AVAILABLE:
            try:
                match = enrich_match_with_league_data(match)
            except Exception as e:
                # Игнорируем ошибки - это дополнительная информация
                pass
        
        filtered.append(match)

    # Сортируем: сначала по коэффициенту (выше = лучше), потом по dominance
    # Это поможет поднять средний коэффициент до 1.2
    # Возвращаем больше матчей для разнообразия
    filtered.sort(key=lambda m: (
        -(m.get("odds_info", OddsInfo(None, None)).value or 0),  # Сначала более высокие коэффициенты
        m.get("dominance_score", 0)  # Потом по dominance
    ), reverse=True)
    # Возвращаем больше матчей, чтобы было из чего выбирать при формировании сообщения
    return filtered[:limit * 2]


def _select_top_tennis_matches(
    limit: int = 2
) -> List[Dict]:
    if limit <= 0:
        return []

    matches = analyze_live_tennis_matches(limit=80)
    
    filtered: List[Dict] = []
    for match in matches:
        # ОБОГАЩАЕМ МАТЧ ИНФОРМАЦИЕЙ О СИЛЕ ИГРОКОВ
        match = enrich_match_with_strength(match)
        
        # Получаем коэффициенты (с мониторингом, если доступен)
        try:
            from monitor_odds_delay import monitor_odds_fetch
            match_minute = match.get("minute_numeric")
            odds = monitor_odds_fetch(
                match["slug"], 
                match["leader_index"], 
                sport="tennis",
                match_minute=match_minute,
                match=match
            )
        except ImportError:
            # Если модуль мониторинга недоступен, используем обычный метод
            # Передаем match для получения реальных коэффициентов с BetBoom
            odds = _get_leader_odds(match["slug"], match["leader_index"], sport="tennis", match=match)
        
        # Проверяем, что odds существует и value не None
        if odds is None or odds.value is None:
            continue
        
        # ПРИМЕНЯЕМ КОРРЕКЦИЮ КОЭФФИЦИЕНТОВ (баскетбол)
        odds_corrected = apply_odds_correction(odds.value)
        match["odds_corrected"] = odds_corrected
        
        # НОВЫЙ ПОДХОД: НЕ фильтруем по коэффициентам - анализируем все матчи по статистике
        points_diff = match.get("points_diff", 0)
        breaks_diff = match.get("breaks_diff", 0)

        dominance = match.get("dominance_score", 0)
        
        # Анализируем матчи по статистике, независимо от коэффициентов
        if True:  # Убрали проверку коэффициентов
            # Матчи в целевом диапазоне 1.15-1.30 (после коррекции)
            current_set = match.get("current_set", 1)
            total_games = match.get("total_games_played", 0)
            
            # Для тенниса учитываем сет: ранние матчи требуют большего перевеса
            if current_set == 1 and total_games < 6:
                # Очень ранний матч - нужен больший перевес
                required_dominance = 6.0
            elif current_set == 1:
                # Первый сет - стандартные требования
                required_dominance = 5.0
            else:
                # Второй сет и дальше - можно немного снизить
                required_dominance = 4.0
            
            # НОВЫЙ ПОДХОД: Проверяем только статистику, без фильтрации по коэффициентам
            # Проверяем dominance и разницу очков
            if dominance >= required_dominance or (points_diff >= 3 and current_set >= 2):
                odds_tier = "safe"
            else:
                continue  # Не прошел проверку по статистике

        match["odds_info"] = odds
        match["odds_tier"] = odds_tier
        match["sport"] = "tennis"
        match["sport_type"] = "tennis"
        names = match.get("teams") or []
        if names:
            match["teams"] = [_transliterate_name(name) for name in names]
        match["score"] = (
            f"{match['sets_score']} ({match['current_games'][0]}:{match['current_games'][1]} "
            f"в {_ordinal_set(match.get('current_set', 1))} сете)"
        )
        match["minute"] = None
        
        filtered.append(match)

    # Сортируем: сначала по коэффициенту (выше = лучше), потом по dominance
    # Это поможет поднять средний коэффициент до 1.2
    # Возвращаем больше матчей для разнообразия
    filtered.sort(key=lambda m: (
        -(m.get("odds_info", OddsInfo(None, None)).value or 0),  # Сначала более высокие коэффициенты
        m.get("dominance_score", 0)  # Потом по dominance
    ), reverse=True)
    # Возвращаем больше матчей, чтобы было из чего выбирать при формировании сообщения
    return filtered[:limit * 2]


def _select_top_basketball_matches(
    limit: int = 3
) -> List[Dict]:
    matches = analyze_live_basketball_matches(limit=120)
    
    filtered: List[Dict] = []
    for match in matches:
        # ОБОГАЩАЕМ МАТЧ ИНФОРМАЦИЕЙ О СИЛЕ КОМАНД
        match = enrich_match_with_strength(match)
        
        # Анализируем все матчи с хоть каким-то перевесом (даже минимальным)
        dominance = match.get("dominance_score", 0)
        if dominance < -5.0:  # Только отфильтровываем явных аутсайдеров
            continue

        # Получаем коэффициенты (с мониторингом, если доступен)
        try:
            from monitor_odds_delay import monitor_odds_fetch
            match_minute = match.get("minute_numeric")
            odds = monitor_odds_fetch(
                match["slug"], 
                match["leader_index"], 
                sport="basketball",
                match_minute=match_minute,
                match=match
            )
        except ImportError:
            # Если модуль мониторинга недоступен, используем обычный метод
            # Передаем match для получения реальных коэффициентов с BetBoom
            odds = _get_leader_odds(match["slug"], match["leader_index"], sport="basketball", match=match)
        
        # Проверяем, что odds существует и value не None
        if odds is None or odds.value is None:
            continue
        
        # ПРИМЕНЯЕМ КОРРЕКЦИЮ КОЭФФИЦИЕНТОВ (баскетбол)
        odds_corrected = apply_odds_correction(odds.value)
        match["odds_corrected"] = odds_corrected
        
        # КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: НЕ фильтруем по коэффициентам до AI анализа
        # Коэффициенты показываем как рекомендацию, а не как фильтр
        # Это позволяет находить больше матчей и давать подписчикам выбор
        # Фильтрация по коэффициентам отключена - анализируем все матчи по статистике
        # if odds_corrected < MIN_ODDS_CORRECTED:
        #     continue  # Слишком низкий коэффициент (после коррекции)
        # if odds_corrected > MAX_ODDS_CORRECTED:
        #     continue  # Слишком высокий коэффициент (после коррекции)

        leader = match["leader_metrics"]
        trailing = match["trailing_metrics"]
        points_diff = leader["points"] - trailing["points"]
        rebounds_diff = leader["rebounds"] - trailing["rebounds"] if not math.isnan(leader["rebounds"]) else 0
        assists_diff = leader["assists"] - trailing["assists"] if not math.isnan(leader["assists"]) else 0

        # КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: Фокус на коэффициенты 1.15-1.30 (ПОСЛЕ коррекции)
        # Проверяем диапазон коэффициентов ПОСЛЕ коррекции
        # НОВЫЙ ПОДХОД: Анализируем все матчи по статистике, без фильтрации по коэффициентам
        minute_numeric = match.get("minute_numeric") or 0
        if True:  # Убрали проверку коэффициентов
            
            # Для баскетбола учитываем время: ранние матчи требуют большего перевеса
            if minute_numeric < 20:  # Меньше половины матча
                required_dominance = 6.0
            elif minute_numeric < 30:
                required_dominance = 5.0
            else:
                required_dominance = 4.0
            
            # НОВЫЙ ПОДХОД: Проверяем только статистику, без фильтрации по коэффициентам
            # Проверяем dominance, разницу очков и подборов
            if dominance >= required_dominance or (points_diff >= 8 and rebounds_diff >= 2 and minute_numeric >= 25):
                odds_tier = "safe"
            else:
                continue  # Не прошел проверку по статистике

        match["odds_info"] = odds
        match["odds_tier"] = odds_tier
        match["sport"] = "basketball"
        match["sport_type"] = "basketball"
        # Транслитерируем названия команд
        names = match.get("teams") or []
        if names:
            match["teams"] = [_transliterate_name(name) for name in names]
        
        filtered.append(match)

    # Сортируем: сначала по коэффициенту (выше = лучше), потом по dominance
    filtered.sort(key=lambda m: (
        -(m.get("odds_info", OddsInfo(None, None)).value or 0),
        m.get("dominance_score", 0)
    ), reverse=True)
    return filtered[:limit * 2]


def _select_top_volleyball_matches(
    limit: int = 2
) -> List[Dict]:
    if limit <= 0:
        return []
    
    matches = analyze_live_volleyball_matches(limit=120)
    
    filtered: List[Dict] = []
    for match in matches:
        # ОБОГАЩАЕМ МАТЧ ИНФОРМАЦИЕЙ О СИЛЕ КОМАНД
        match = enrich_match_with_strength(match)
        
        dominance = match.get("dominance_score", 0)
        if dominance < 5.0:
            continue
        
        # Получаем коэффициенты
        try:
            from monitor_odds_delay import monitor_odds_fetch
            odds = monitor_odds_fetch(
                match["slug"], 
                match["leader_index"], 
                sport="volleyball",
                match=match
            )
        except ImportError:
            odds = _get_leader_odds(match["slug"], match["leader_index"], sport="volleyball", match=match)
        
        if odds is None or odds.value is None:
            continue
        
        odds_corrected = apply_odds_correction(odds.value)
        match["odds_corrected"] = odds_corrected
        
        match["odds_info"] = odds
        match["sport"] = "volleyball"
        match["sport_type"] = "volleyball"
        names = match.get("teams") or []
        if names:
            match["teams"] = [_transliterate_name(name) for name in names]
        
        filtered.append(match)
    
    filtered.sort(key=lambda m: (
        -(m.get("odds_info", OddsInfo(None, None)).value or 0),
        m.get("dominance_score", 0)
    ), reverse=True)
    return filtered[:limit * 2]


def _select_top_american_football_matches(
    limit: int = 2
) -> List[Dict]:
    if limit <= 0:
        return []
    
    matches = analyze_live_american_football_matches(limit=120)
    
    filtered: List[Dict] = []
    for match in matches:
        match = enrich_match_with_strength(match)
        
        dominance = match.get("dominance_score", 0)
        if dominance < 5.0:
            continue
        
        try:
            from monitor_odds_delay import monitor_odds_fetch
            odds = monitor_odds_fetch(
                match["slug"], 
                match["leader_index"], 
                sport="american-football",
                match=match
            )
        except ImportError:
            odds = _get_leader_odds(match["slug"], match["leader_index"], sport="american-football", match=match)
        
        if odds is None or odds.value is None:
            continue
        
        odds_corrected = apply_odds_correction(odds.value)
        match["odds_corrected"] = odds_corrected
        
        match["odds_info"] = odds
        match["sport"] = "american_football"
        match["sport_type"] = "american_football"
        names = match.get("teams") or []
        if names:
            match["teams"] = [_transliterate_name(name) for name in names]
        
        filtered.append(match)
    
    filtered.sort(key=lambda m: (
        -(m.get("odds_info", OddsInfo(None, None)).value or 0),
        m.get("dominance_score", 0)
    ), reverse=True)
    return filtered[:limit * 2]


def _select_top_dota2_matches(
    limit: int = 2
) -> List[Dict]:
    if limit <= 0:
        return []
    
    matches = analyze_live_dota2_matches(limit=120)
    
    filtered: List[Dict] = []
    for match in matches:
        match = enrich_match_with_strength(match)
        
        dominance = match.get("dominance_score", 0)
        if dominance < 5.0:
            continue
        
        try:
            from monitor_odds_delay import monitor_odds_fetch
            odds = monitor_odds_fetch(
                match["slug"], 
                match["leader_index"], 
                sport="dota2",
                match=match
            )
        except ImportError:
            odds = _get_leader_odds(match["slug"], match["leader_index"], sport="dota2", match=match)
        
        if odds is None or odds.value is None:
            continue
        
        odds_corrected = apply_odds_correction(odds.value)
        match["odds_corrected"] = odds_corrected
        
        match["odds_info"] = odds
        match["sport"] = "dota2"
        match["sport_type"] = "dota2"
        names = match.get("teams") or []
        if names:
            match["teams"] = [_transliterate_name(name) for name in names]
        
        filtered.append(match)
    
    filtered.sort(key=lambda m: (
        -(m.get("odds_info", OddsInfo(None, None)).value or 0),
        m.get("dominance_score", 0)
    ), reverse=True)
    return filtered[:limit * 2]


def _get_leader_odds(slug: str, leader_index: int, sport: str = "soccer", match: Optional[Dict] = None) -> OddsInfo:
    """
    Получает коэффициенты лидера с автоматической коррекцией завышенных значений Scores24.
    
    Коэффициенты Scores24 автоматически корректируются на основе статистики.
    Для обучения корректора используй odds_corrector.log_odds_comparison()
    
    Args:
        slug: Slug матча
        leader_index: Индекс лидера (0 или 1)
        sport: Вид спорта
        match: Словарь с данными матча (не используется, оставлен для совместимости)
    """
    # Получаем коэффициенты с Scores24
    desired_outcome = "w1" if leader_index == 0 else "w2"
    # Для футбола используем "one_x_two", для остальных видов спорта - "one_two"
    preferred_market = "one_x_two" if sport == "soccer" else "one_two"
    odds_markets = fetch_match_odds(slug, market=None, limit=5, market_limit=5, sport=sport)

    preferred_value: Optional[float] = None
    preferred_bookmaker: Optional[str] = None
    fallback_value: Optional[float] = None
    fallback_bookmaker: Optional[str] = None

    for market in odds_markets:
        market_name = market.get("market")
        if market_name not in {preferred_market, "one_x_two", "one_two"}:
            continue
        for rate in market.get("topRates", []):
            for value in rate.get("values", []):
                if value.get("outcome") != desired_outcome:
                    continue
                coeff_raw = value.get("value")
                try:
                    coeff = float(coeff_raw) if coeff_raw is not None else None
                except (TypeError, ValueError):
                    continue
                bookmaker_info = value.get("bookmaker")
                if bookmaker_info and isinstance(bookmaker_info, dict):
                    bookmaker = bookmaker_info.get("name") or "Unknown"
                else:
                    bookmaker = "Unknown"
                
                # Приоритет BetBoom, но используем любой доступный коэффициент
                if bookmaker and "betboom" in bookmaker.lower():
                    if coeff and not preferred_value:  # Используем BetBoom если есть
                        preferred_value = coeff
                        preferred_bookmaker = "BetBoom"
                # Всегда сохраняем fallback - любой доступный коэффициент
                if coeff and (fallback_value is None or coeff > fallback_value):
                    fallback_value = coeff
                    fallback_bookmaker = bookmaker
            if preferred_value is not None:
                break
        if preferred_value is not None:
            break

    # Применяем коррекцию к коэффициентам Scores24
    try:
        from odds_corrector import correct_scores24_odds
        
        if preferred_value is not None:
            corrected_value = correct_scores24_odds(preferred_value)
            return OddsInfo(corrected_value, preferred_bookmaker or "BetBoom (corrected)")
        
        if fallback_value is not None:
            corrected_value = correct_scores24_odds(fallback_value)
            return OddsInfo(corrected_value, fallback_bookmaker or "Scores24 (corrected)")
    except ImportError:
        # Модуль коррекции недоступен, возвращаем без коррекции
        pass
    except Exception as e:
        log_warning(f"Failed to correct odds, using original: {e}")
    
    # Fallback без коррекции
    if preferred_value is not None:
        return OddsInfo(preferred_value, preferred_bookmaker)
    if fallback_value is not None:
        return OddsInfo(fallback_value, fallback_bookmaker)
    return OddsInfo(None, None)


def _estimate_probability(match: Dict) -> int:
    leader = match["leader_metrics"]
    trailing = match["trailing_metrics"]

    # xG опциональный
    xg_diff = 0.0
    if not math.isnan(leader["xg"]) and not math.isnan(trailing["xg"]):
        xg_diff = leader["xg"] - trailing["xg"]
    
    shots_ot_diff = leader["shots_on_target"] - trailing["shots_on_target"]
    shots_total_diff = 0.0
    if not math.isnan(leader["shots_total"]) and not math.isnan(trailing["shots_total"]):
        shots_total_diff = leader["shots_total"] - trailing["shots_total"]
    possession_diff = leader["possession"] - trailing["possession"]
    score_gap = abs(match["home_score"] - match["away_score"])

    foot_floor = int(round(getattr(TUNING_SETTINGS, "football_probability_floor", PROBABILITY_MIN / 100) * 100))
    foot_cap = int(round(getattr(TUNING_SETTINGS, "football_probability_cap", PROBABILITY_MAX / 100) * 100))

    base_prob = (
        60
        + xg_diff * 8
        + max(0, shots_ot_diff) * 4
        + max(0, shots_total_diff) * 1.2
        + max(0, possession_diff) * 0.12
        + score_gap * 3.5
    )
    
    # КОРРЕКТИРОВКА С УЧЕТОМ СИЛЫ КОМАНД
    try:
        strength_diff = match.get("strength_diff", 0)
        if strength_diff:
            # Корректируем вероятность на основе разницы силы
            # Разница силы 10 пунктов = +2% к вероятности
            strength_adjustment = (strength_diff / 10.0) * 2.0
            base_prob += strength_adjustment
    except:
        pass
    
    probability = max(foot_floor, min(foot_cap, base_prob))
    
    # КОРРЕКТИРОВКА С УЧЕТОМ ИСТОРИЧЕСКИХ ДАННЫХ
    try:
        teams = match.get("teams", [])
        leader_idx = match.get("leader_index", 0)
        tournament = match.get("tournament") or match.get("tournament_name", "")
        country = match.get("country", "")
        if isinstance(country, dict):
            country = country.get("name", "")
        
        if len(teams) >= 2:
            team1_name = teams[0]
            team2_name = teams[1]
            leader_name = teams[leader_idx]
            
            # Корректируем вероятность с учетом исторических данных
            adjusted_prob, history_factors = adjust_probability_with_history(
                base_probability=probability,
                team1_name=team1_name,
                team2_name=team2_name,
                sport="football",
                league=tournament,
                team1_is_leader=(leader_idx == 0)
            )
            
            # Сохраняем исторические факторы в матч для использования в анализе
            match["history_factors"] = history_factors
            
            probability = adjusted_prob
    except Exception as e:
        # Если ошибка при получении исторических данных, используем базовую вероятность
        pass
    
    return int(round(probability))


def _estimate_tennis_probability(match: Dict) -> int:
    sets_parts = match.get("sets_score", "0:0").split(":")
    try:
        sets_home = int(sets_parts[0])
        sets_away = int(sets_parts[1])
    except (ValueError, IndexError):
        sets_home = sets_away = 0

    leader_idx = match["leader_index"]
    trailing_idx = 1 - leader_idx
    set_advantage = (sets_home - sets_away) if leader_idx == 0 else (sets_away - sets_home)

    games = match.get("current_games") or (0, 0)
    games_leader = games[leader_idx]
    games_trailing = games[trailing_idx] if trailing_idx < len(games) else 0
    games_diff = games_leader - games_trailing

    points_diff = match.get("points_diff", 0)
    breaks_diff = match.get("breaks_diff", 0)
    dominance = match.get("dominance_score", 0)

    tennis_floor = int(round(getattr(TUNING_SETTINGS, "tennis_probability_floor", PROBABILITY_MIN / 100) * 100))
    tennis_cap = int(round(getattr(TUNING_SETTINGS, "tennis_probability_cap", PROBABILITY_MAX / 100) * 100))

    base_prob = (
        58
        + set_advantage * 10
        + max(games_diff, 0) * 3
        + max(points_diff, 0) * 1.0
        + max(breaks_diff, 0) * 8
        + min(dominance, 25) * 0.5
    )
    
    # КОРРЕКТИРОВКА С УЧЕТОМ СИЛЫ ИГРОКОВ
    try:
        strength_diff = match.get("strength_diff", 0)
        if strength_diff:
            # Корректируем вероятность на основе разницы силы
            # Разница силы 10 пунктов = +3% к вероятности (теннис более предсказуем)
            strength_adjustment = (strength_diff / 10.0) * 3.0
            base_prob += strength_adjustment
    except:
        pass
    
    probability = max(tennis_floor, min(tennis_cap, base_prob))
    return int(round(probability))


def _estimate_volleyball_probability(match: Dict) -> int:
    """Оценивает вероятность победы лидера в волейболе"""
    dominance = match.get("dominance_score", 0)
    sets_score = match.get("sets_score", "0:0")
    current_set_score = match.get("current_set_score", (0, 0))
    
    sets_home, sets_away = sets_score.split(":") if ":" in sets_score else ("0", "0")
    sets_home_int = int(sets_home) if sets_home.isdigit() else 0
    sets_away_int = int(sets_away) if sets_away.isdigit() else 0
    set_diff = abs(sets_home_int - sets_away_int)
    
    points_diff = abs(current_set_score[0] - current_set_score[1]) if len(current_set_score) == 2 else 0
    
    # Базовая вероятность на основе dominance
    base_prob = 65 + min(dominance * 2, 25)
    
    # Бонус за преимущество по сетам
    if set_diff >= 2:
        base_prob += 10
    elif set_diff == 1:
        base_prob += 5
    
    # Бонус за разницу в очках в текущем сете
    if points_diff >= 5:
        base_prob += 5
    elif points_diff >= 3:
        base_prob += 3
    
    return min(int(round(base_prob)), 90)


def _estimate_american_football_probability(match: Dict) -> int:
    """Оценивает вероятность победы лидера в американском футболе"""
    dominance = match.get("dominance_score", 0)
    score_diff = match.get("score_diff", 0)
    minute_numeric = match.get("minute_numeric", 0)
    
    # Базовая вероятность на основе dominance
    base_prob = 65 + min(dominance * 1.5, 25)
    
    # Бонус за разницу в очках
    if score_diff >= 14:
        base_prob += 8
    elif score_diff >= 10:
        base_prob += 5
    elif score_diff >= 7:
        base_prob += 3
    
    # Бонус за время матча (позже = выше вероятность)
    if minute_numeric >= 45:
        base_prob += 5
    elif minute_numeric >= 30:
        base_prob += 3
    
    return min(int(round(base_prob)), 90)


def _estimate_dota2_probability(match: Dict) -> int:
    """Оценивает вероятность победы лидера в текущей карте Dota 2"""
    dominance = match.get("dominance_score", 0)
    current_map_score = match.get("current_map_score", (0, 0))
    kills_diff = abs(current_map_score[0] - current_map_score[1]) if len(current_map_score) == 2 else 0
    net_worth = match.get("net_worth") or match.get("gold")
    game_time = match.get("game_time", 0)
    
    # Базовая вероятность на основе dominance
    base_prob = 65 + min(dominance * 1.5, 25)
    
    # Бонус за разницу в убийствах
    if kills_diff >= 10:
        base_prob += 8
    elif kills_diff >= 7:
        base_prob += 5
    elif kills_diff >= 5:
        base_prob += 3
    
    # Бонус за Net Worth (если лидер впереди)
    if net_worth:
        net_worth_diff = net_worth[0] - net_worth[1] if match.get("leader_index") == 0 else net_worth[1] - net_worth[0]
        if net_worth_diff >= 5000:
            base_prob += 5
        elif net_worth_diff >= 3000:
            base_prob += 3
        elif net_worth_diff >= 2000:
            base_prob += 1
    
    # Бонус за время игры (больше времени = выше вероятность)
    if game_time >= 40:
        base_prob += 3
    elif game_time >= 30:
        base_prob += 1
    
    return min(int(round(base_prob)), 90)


def _estimate_handball_probability(match: Dict) -> int:
    minute = match.get("minute_numeric") or 0
    score_diff = match.get("score_diff", 0)
    pace = match.get("pace", 0)
    projected = match.get("projected_total") or (match.get("total_score") or 0)
    remaining = max(0, 60 - minute)
    base_prob = (
        60
        + score_diff * 6
        + max(0, pace - 1) * 4
        + max(0, projected - 55) * 0.3
        - remaining * 0.25
    )
    
    # КОРРЕКТИРОВКА С УЧЕТОМ СИЛЫ КОМАНД
    try:
        strength_diff = match.get("strength_diff", 0)
        if strength_diff:
            strength_adjustment = (strength_diff / 10.0) * 2.0
            base_prob += strength_adjustment
    except:
        pass
    
    probability = max(58, min(94, base_prob))
    return int(round(probability))


def _format_odds_line(match: Dict, probability: float) -> str:
    """
    Форматирует строку с коэффициентом и EV.
    
    Args:
        match: Словарь с данными матча
        probability: Вероятность в процентах
    
    Returns:
        Отформатированная строка или пустая строка, если коэффициента нет
    """
    odds_info = match.get("odds_info")
    if not odds_info:
        return ""
    
    odds_value = None
    if hasattr(odds_info, "value"):
        odds_value = odds_info.value
    elif isinstance(odds_info, dict):
        odds_value = odds_info.get("value")
    
    # Используем скорректированный коэффициент для отображения
    odds_corrected = match.get("odds_corrected")
    if odds_corrected:
        odds_value = odds_corrected
    
    if not odds_value:
        return ""
    
    # НОВЫЙ ПОДХОД: Показываем рекомендуемый коэффициент вместо текущего
    try:
        from recommended_odds_calculator import format_odds_recommendation
        odds_recommendation = format_odds_recommendation(match)
        return odds_recommendation
    except ImportError:
        # Fallback: старый формат
        odds_line = f"💰 Коэффициент: {odds_value:.2f}"
        
        # Добавляем EV
        try:
            from roi_optimizer import calculate_expected_value
            ev = calculate_expected_value(probability, odds_value)
            if ev >= 0:
                odds_line += f" | EV: +{ev*100:.1f}%"
            else:
                odds_line += f" | EV: {ev*100:.1f}%"
        except ImportError:
            pass
        
        return odds_line
    
    return odds_line


def _format_positions(match: Dict) -> str:
    positions = match.get("positions") or {}
    home, away = match["teams"]
    home_pos = positions.get(home)
    away_pos = positions.get(away)
    if home_pos or away_pos:
        home_txt = f"{home}: {home_pos}-е место" if home_pos else f"{home}: позиция не указана"
        away_txt = f"{away}: {away_pos}-е место" if away_pos else f"{away}: позиция не указана"
        return f"{home_txt} | {away_txt}"
    return "данные по таблице отсутствуют"


def _ordinal_set(value: int) -> str:
    if value == 1:
        return "1-м"
    if value == 2:
        return "2-м"
    if value == 3:
        return "3-м"
    return f"{value}-м"


def _bold_team_names_in_text(text: str, teams: List[str]) -> str:
    """Выделяет названия команд жирным в тексте (Markdown отключен, возвращаем как есть)."""
    # Markdown отключен из-за ошибок парсинга в Telegram
    # Возвращаем текст без изменений
    return text


def _get_control_phrase_variation(leader_name: str, context: str = "game") -> str:
    """
    Возвращает случайную вариацию фразы о контроле матча/игры.
    
    Args:
        leader_name: Имя лидера
        context: Контекст - "game" (игра), "set" (сет), "match" (матч)
    
    Returns:
        Случайная фраза о контроле
    """
    import random
    
    if context == "set":
        # Вариации для тенниса/волейбола (контроль сета)
        variations = [
            f"<b>{leader_name}</b> контролирует",
            f"<b>{leader_name}</b> доминирует в",
            f"<b>{leader_name}</b> уверенно ведёт",
            f"<b>{leader_name}</b> превосходит соперника в",
            f"<b>{leader_name}</b> имеет явное преимущество в",
            f"<b>{leader_name}</b> задаёт тон в",
            f"<b>{leader_name}</b> управляет ходом",
        ]
    else:
        # Вариации для футбола/баскетбола (контроль игры/матча)
        variations = [
            f"<b>{leader_name}</b> контролирует игру",
            f"<b>{leader_name}</b> доминирует на площадке",
            f"<b>{leader_name}</b> уверенно ведёт матч",
            f"<b>{leader_name}</b> превосходит соперника",
            f"<b>{leader_name}</b> имеет явное преимущество",
            f"<b>{leader_name}</b> задаёт тон игры",
            f"<b>{leader_name}</b> управляет ходом матча",
            f"<b>{leader_name}</b> уверенно контролирует ситуацию",
            f"<b>{leader_name}</b> демонстрирует превосходство",
            f"<b>{leader_name}</b> удерживает инициативу",
        ]
    
    return random.choice(variations)


def _format_analysis(match: Dict) -> str:
    leader_idx = match["leader_index"]
    trailing_idx = 1 - leader_idx
    leader_name = match["teams"][leader_idx]
    trailing_name = match["teams"][trailing_idx]
    score = match["score"]
    minute = _format_minute(match.get("minute"), match.get("status_code"))

    leader = match["leader_metrics"]
    trailing = match["trailing_metrics"]

    parts: List[str] = []
    # xG опциональный - используем только если есть
    if not math.isnan(leader["xg"]) and not math.isnan(trailing["xg"]):
        xg_diff = leader["xg"] - trailing["xg"]
        if xg_diff >= 0.15:
            parts.append(f"xG {leader['xg']:.2f} против {trailing['xg']:.2f}")
    shots_ot_diff = leader["shots_on_target"] - trailing["shots_on_target"]
    if shots_ot_diff >= 1:
        parts.append(
            f"удары в створ {int(round(leader['shots_on_target']))}-{int(round(trailing['shots_on_target']))}"
        )
    # shots_total опциональный
    if not math.isnan(leader["shots_total"]) and not math.isnan(trailing["shots_total"]):
        shots_total_diff = leader["shots_total"] - trailing["shots_total"]
        if shots_total_diff >= 2:
            parts.append(f"всего ударов {int(round(leader['shots_total']))}-{int(round(trailing['shots_total']))}")
    possession_diff = leader["possession"] - trailing["possession"]
    if possession_diff >= 5:
        parts.append(
            f"владение {int(round(leader['possession']))}% против {int(round(trailing['possession']))}%"
        )

    if not parts:
        # Если xG нет, используем удары в створ как основную метрику
        if not math.isnan(leader["xg"]) and not math.isnan(trailing["xg"]):
            parts.append(f"xG {leader['xg']:.2f} против {trailing['xg']:.2f}")
        else:
            parts.append(f"удары в створ {int(round(leader['shots_on_target']))}-{int(round(trailing['shots_on_target']))}")

    # Вариации фразы о преимуществе
    advantage_phrases = [
        f"подтверждает преимущество по",
        f"демонстрирует превосходство по",
        f"показывает доминирование по",
        f"укрепляет позиции по",
        f"закрепляет лидерство по",
        f"поддерживает перевес по",
    ]
    import random
    advantage_phrase = random.choice(advantage_phrases)
    
    analysis = (
        f"<b>{leader_name}</b> ведет {score} на {minute}' и {advantage_phrase} {', '.join(parts)}."
    )

    if trailing["shots_on_target"] <= 1:
        analysis += f" <b>{trailing_name}</b> создал лишь {int(round(trailing['shots_on_target']))} опасный момент."
    else:
        analysis += f" <b>{trailing_name}</b> пока отвечает реже, но уступает по качеству моментов."

    return analysis


def _format_tennis_block(index: int, match: Dict) -> str:
    def _safe_int(value: Optional[float]) -> int:
        if value is None:
            return 0
        try:
            if isinstance(value, float) and math.isnan(value):
                return 0
            return int(round(float(value)))
        except (TypeError, ValueError):
            return 0

    leader_idx = match["leader_index"]
    teams = match["teams"]
    leader_name = teams[leader_idx]
    opponent_name = teams[1 - leader_idx]
    sets_score = match.get("sets_score", "0:0")
    games_home, games_away = match.get("current_games", (0, 0))
    current_set = match.get("current_set", 1)
    tournament = match.get("tournament")
    country = match.get("country")
    location_parts = [part for part in (country, tournament) if part]
    location = " • ".join(location_parts) if location_parts else "—"

    probability = _estimate_tennis_probability(match)
    match["estimated_probability"] = probability

    points = match.get("points") or (0, 0)
    breakpoints_won = match.get("breakpoints_won")
    total_breakpoints = match.get("total_breakpoints")
    aces = match.get("aces")
    double_faults = match.get("double_faults")
    service_points_won = match.get("service_points_won")

    stats_lines = [
        f"* Очки: {_safe_int(points[0])} - {_safe_int(points[1])}",
    ]

    if breakpoints_won and all(not math.isnan(x) for x in breakpoints_won if isinstance(x, float)):
        if total_breakpoints:
            bp_home = f"{_safe_int(breakpoints_won[0])}/{_safe_int(total_breakpoints[0])}"
            bp_away = f"{_safe_int(breakpoints_won[1])}/{_safe_int(total_breakpoints[1])}"
            stats_lines.append(f"* Брейк-пойнты: {bp_home} - {bp_away}")
        else:
            stats_lines.append(
                f"* Брейк-пойнты: {_safe_int(breakpoints_won[0])} - {_safe_int(breakpoints_won[1])}"
            )
    if aces or double_faults:
        aces_text = _safe_int(aces[0] if aces else 0)
        aces_away = _safe_int(aces[1] if aces else 0)
        df_home = _safe_int(double_faults[0] if double_faults else 0)
        df_away = _safe_int(double_faults[1] if double_faults else 0)
        stats_lines.append(f"* Эйсы: {aces_text} - {aces_away} • Двойные: {df_home} - {df_away}")
    if service_points_won and all(
        not math.isnan(x) for x in service_points_won if isinstance(x, float)
    ):
        stats_lines.append(
            f"* Очки на подаче: {_safe_int(service_points_won[0])} - {_safe_int(service_points_won[1])}"
        )

    analysis_parts: List[str] = []
    # Исправляем логику: если счет по сетам 0:0 или 1:1 (ничья), не пишем "ведёт"
    sets_home, sets_away = sets_score.split(":") if ":" in sets_score else ("0", "0")
    sets_home_int = int(sets_home) if sets_home.isdigit() else 0
    sets_away_int = int(sets_away) if sets_away.isdigit() else 0
    
    import random
    
    if sets_score == "0:0":
        control_phrase = _get_control_phrase_variation(leader_name, "set")
        analysis_parts.append(
            f"{control_phrase} {_ordinal_set(current_set)} сет {games_home}:{games_away}."
        )
    elif sets_home_int == sets_away_int:
        # Ничья по сетам (например, 1:1) - не пишем "ведёт"
        control_phrase = _get_control_phrase_variation(leader_name, "set")
        analysis_parts.append(
            f"Счет по сетам {sets_score} (ничья). {control_phrase} {_ordinal_set(current_set)} сет "
            f"{games_home}:{games_away}."
        )
    else:
        # Вариации для "ведёт по сетам и контролирует"
        leading_variations = [
            f"<b>{leader_name}</b> ведёт по сетам {sets_score} и",
            f"<b>{leader_name}</b> лидирует {sets_score} по сетам и",
            f"<b>{leader_name}</b> опережает соперника {sets_score} и",
            f"Счет по сетам {sets_score} в пользу <b>{leader_name}</b>, который",
        ]
        leading_phrase = random.choice(leading_variations)
        control_phrase = _get_control_phrase_variation(leader_name, "set").replace(f"<b>{leader_name}</b> ", "")
        analysis_parts.append(
            f"{leading_phrase} {control_phrase} {_ordinal_set(current_set)} сет {games_home}:{games_away}."
        )
    points_diff = match.get("points_diff", 0)
    if points_diff >= 4:
        analysis_parts.append(
            f"По очкам <b>{leader_name}</b> впереди {_safe_int(points[leader_idx])} против {_safe_int(points[1 - leader_idx])}."
        )
    breaks_diff = match.get("breaks_diff", 0)
    if breaks_diff >= 1 and breakpoints_won:
        analysis_parts.append(
            f"Лидер уже реализовал {_safe_int(breakpoints_won[leader_idx])} брейк(а) против {_safe_int(breakpoints_won[1 - leader_idx])}."
        )
    if match.get("odds_tier") == "extended":
        analysis_parts.append("Коэффициент в контрольном диапазоне — сокращаем размер ставки.")

    analysis = " ".join(analysis_parts)
    bet_side = "П1" if leader_idx == 0 else "П2"

    # Добавляем анализ ИИ, если есть
    ai_note = ""
    if match.get("gpt_analysis_unavailable"):
        # GPT анализ недоступен - показываем предупреждение жирным шрифтом
        ai_note = f"\n<b>⚠️ GPT анализ недоступен. Используется внутренний алгоритм оценки.</b>"
    elif match.get("claude_probability"):
        ai_prob = match.get("claude_probability")
        ai_rec = match.get("claude_recommendation", "")
        ai_source = match.get("ai_source", "unknown")
        
        # Определяем название ИИ для отображения
        if "gpt" in ai_source.lower() or "aitunnel_gpt" in ai_source.lower():
            ai_name = "CHAT GPT AI"
        elif "claude" in ai_source.lower():
            ai_name = "Claude AI"  # На случай, если в будущем включим
        else:
            ai_name = "ИИ"
        
        if ai_rec:
            ai_note = f"\n🤖 {ai_name}: {ai_rec}"
        # Используем вероятность от ИИ, если она есть
        if ai_prob and ai_prob > 0:
            probability = ai_prob
    
    # Добавляем пометку "!повтор!" если матч уже был отправлен
    repeat_prefix = "!повтор! " if match.get("is_repeat", False) else ""
    
    # Добавляем пометку стратегии
    strategy_label = ""
    strategy = match.get("strategy")
    if strategy == "set_break":
        strategy_label = " ⚡ СЕТ-БРЕЙК"
    
    block = [
        f"{index}. {repeat_prefix}🎾 <b>{teams[0]}</b> - <b>{teams[1]}</b>{strategy_label}",
        f"🏟️ {location}",
        f"📊 Счёт: {sets_score} по сетам, {games_home}:{games_away} в {_ordinal_set(current_set)} сете • {bet_side} <b>{leader_name}</b>",
        "📈 " + " | ".join(stats_lines),
        f"🎯 {analysis}{ai_note}",
        f"⚡ <b>ВЕРОЯТНОСТЬ: ~{probability}%</b>",
    ]
    
    # Добавляем информацию о коэффициенте и Expected Value
    odds_info = match.get("odds_info")
    if odds_info:
        odds_value = None
        if hasattr(odds_info, "value"):
            odds_value = odds_info.value
        elif isinstance(odds_info, dict):
            odds_value = odds_info.get("value")
        
        # Используем скорректированный коэффициент для отображения
        odds_corrected = match.get("odds_corrected")
        if odds_corrected:
            odds_value = odds_corrected
        
        if odds_value:
            odds_line = f"💰 Коэффициент: {odds_value:.2f}"
            
            # Добавляем EV
            try:
                from roi_optimizer import calculate_expected_value
                ev = calculate_expected_value(probability, odds_value)
                if ev >= 0:
                    odds_line += f" | EV: +{ev*100:.1f}%"
                else:
                    odds_line += f" | EV: {ev*100:.1f}%"
            except ImportError:
                pass
            
            
            block.append(odds_line)
    
    return "\n".join(block)


def _format_handball_block(index: int, match: Dict) -> str:
    leader_idx = match["leader_index"]
    teams = match["teams"]
    leader_name = teams[leader_idx]
    score = match["score"]
    minute = match.get("minute")
    tournament = match.get("tournament")
    country = match.get("country")
    location_parts = [part for part in (country, tournament) if part]
    location = " • ".join(location_parts) if location_parts else "—"

    probability = _estimate_handball_probability(match)
    match["estimated_probability"] = probability

    total_score = match.get("total_score", 0)
    score_diff = match.get("score_diff", 0)
    pace = match.get("pace", 0)
    projected_total = match.get("projected_total")
    total_recommendation = match.get("total_recommendation")
    minute_numeric = match.get("minute_numeric")
    
    # Используем числовое значение минуты для правильного расчета темпа
    if minute_numeric is None and minute:
        try:
            # Парсим минуту из строки (например, "37'", "43 мин", "37")
            minute_str = str(minute).strip()
            minute_match = re.search(r"(\d+)", minute_str)
            if minute_match:
                minute_numeric = int(minute_match.group(1))
        except (ValueError, AttributeError):
            minute_numeric = None
    
    if minute_numeric:
        stats_lines = [
            f"* Счёт: {score} (отрыв {score_diff})",
            f"* Темп: {total_score} голов за {minute_numeric} мин (≈ {pace:.2f} гол/мин)",
        ]
    else:
        stats_lines = [
            f"* Счёт: {score} (отрыв {score_diff})",
            f"* Темп: {total_score} голов (минута не определена)",
        ]
    if projected_total:
        stats_lines.append(f"* Прогнозный тотал: {projected_total:.1f}")
    if total_recommendation:
        stats_lines.append(
            f"* Тотал: рекомендую {total_recommendation['label']} {total_recommendation['value']} (если линия доступна)"
        )

    import random
    
    analysis_parts: List[str] = []
    # Вариации фразы о контроле игры
    control_phrase = _get_control_phrase_variation(leader_name, "game")
    analysis_parts.append(
        f"{control_phrase} — ведёт {score_diff} мяч(а) на {minute}-й минуте."
    )
    if projected_total:
        analysis_parts.append(
            f"Темп {pace:.2f} гол/мин даёт прогноз ≈ {projected_total:.1f}."
        )
    if total_recommendation:
        if total_recommendation["type"] == "over":
            analysis_parts.append(
                f"Игра открытая — рассматриваем {total_recommendation['label']} {total_recommendation['value']}."
            )
        else:
            analysis_parts.append(
                f"Темп снижается — рассматриваем {total_recommendation['label']} {total_recommendation['value']}."
            )
        analysis_parts.append("Учти: у букмекера нужного тотала может не быть.")

    analysis = " ".join(analysis_parts)
    bet_side = "П1" if leader_idx == 0 else "П2"

    # Добавляем пометку "!повтор!" если матч уже был отправлен
    repeat_prefix = "!повтор! " if match.get("is_repeat", False) else ""
    
    block = [
        f"{index}. {repeat_prefix}🤾 <b>{teams[0]}</b> - <b>{teams[1]}</b>",
        f"🏟️ {location}",
        f"📊 Счёт: {score} ({minute}' мин)",
        f"✅ Ставка: {bet_side} <b>{leader_name}</b>",
        "",
        "📈 РЕАЛЬНАЯ СТАТИСТИКА:",
        "\n".join(stats_lines),
        "",
        "🎯 АНАЛИЗ:",
        analysis,
        "",
        f"⚡ <b>ВЕРОЯТНОСТЬ: ~{probability}%</b>",
    ]
    
    # Добавляем информацию о коэффициенте и Expected Value
    odds_info = match.get("odds_info")
    if odds_info:
        odds_value = None
        if hasattr(odds_info, "value"):
            odds_value = odds_info.value
        elif isinstance(odds_info, dict):
            odds_value = odds_info.get("value")
        
        # Используем скорректированный коэффициент для отображения
        odds_corrected = match.get("odds_corrected")
        if odds_corrected:
            odds_value = odds_corrected
        
        odds_line = _format_odds_line(match, probability)
        if odds_line:
            block.append(odds_line)
    
    return "\n".join(block)


def _format_volleyball_block(index: int, match: Dict) -> str:
    leader_idx = match["leader_index"]
    teams = match["teams"]
    leader_name = teams[leader_idx]
    sets_score = match.get("sets_score", "0:0")
    current_set_score = match.get("current_set_score", (0, 0))
    current_set = match.get("current_set", 1)
    tournament = match.get("tournament")
    country = match.get("country")
    location_parts = [part for part in (country, tournament) if part]
    location = " • ".join(location_parts) if location_parts else "—"
    
    probability = match.get("claude_probability") or _estimate_volleyball_probability(match)
    match["estimated_probability"] = probability
    
    analysis_parts: List[str] = []
    sets_home, sets_away = sets_score.split(":") if ":" in sets_score else ("0", "0")
    sets_home_int = int(sets_home) if sets_home.isdigit() else 0
    sets_away_int = int(sets_away) if sets_away.isdigit() else 0
    
    import random
    
    if sets_home_int == sets_away_int:
        control_phrase = _get_control_phrase_variation(leader_name, "set")
        analysis_parts.append(
            f"Счет по сетам {sets_score} (ничья). {control_phrase} {current_set} сет "
            f"{current_set_score[0]}:{current_set_score[1]}."
        )
    else:
        leading_variations = [
            f"<b>{leader_name}</b> ведёт по сетам {sets_score} и",
            f"<b>{leader_name}</b> лидирует {sets_score} по сетам и",
            f"<b>{leader_name}</b> опережает соперника {sets_score} и",
            f"Счет по сетам {sets_score} в пользу <b>{leader_name}</b>, который",
        ]
        leading_phrase = random.choice(leading_variations)
        control_phrase = _get_control_phrase_variation(leader_name, "set").replace(f"<b>{leader_name}</b> ", "")
        analysis_parts.append(
            f"{leading_phrase} {control_phrase} {current_set} сет {current_set_score[0]}:{current_set_score[1]}."
        )
    
    bet_side = "П1" if leader_idx == 0 else "П2"
    repeat_prefix = "!повтор! " if match.get("is_repeat", False) else ""
    
    block = [
        f"{index}. {repeat_prefix}🏐 <b>{teams[0]}</b> - <b>{teams[1]}</b>",
        f"🏟️ {location}",
        f"📊 Счёт: {sets_score} по сетам, {current_set_score[0]}:{current_set_score[1]} в {current_set} сете • {bet_side} <b>{leader_name}</b>",
        f"🎯 {' '.join(analysis_parts)}",
        f"⚡ <b>ВЕРОЯТНОСТЬ: ~{probability}%</b>",
    ]
    
    odds_info = match.get("odds_info")
    if odds_info:
        odds_value = odds_info.value if hasattr(odds_info, "value") else odds_info.get("value") if isinstance(odds_info, dict) else None
        odds_corrected = match.get("odds_corrected")
        if odds_corrected:
            odds_value = odds_corrected
        if odds_value:
            odds_line = _format_odds_line(match, probability)
            if odds_line:
                block.append(odds_line)
    
    return "\n".join(block)


def _format_american_football_block(index: int, match: Dict) -> str:
    leader_idx = match["leader_index"]
    teams = match["teams"]
    leader_name = teams[leader_idx]
    score = match["score"]
    minute = _format_minute(match.get("minute"), match.get("status_code"))
    tournament = match.get("tournament")
    country = match.get("country")
    location_parts = [part for part in (country, tournament) if part]
    location = " • ".join(location_parts) if location_parts else "—"
    
    probability = match.get("claude_probability") or _estimate_american_football_probability(match)
    match["estimated_probability"] = probability
    score_diff = match.get("score_diff", 0)
    
    minute_display = f"{minute}'" if minute and minute != "—" and minute != "?" else "live"
    
    import random
    
    analysis_parts: List[str] = []
    # Вариации фразы о контроле игры
    control_phrase = _get_control_phrase_variation(leader_name, "game")
    analysis_parts.append(
        f"{control_phrase} — ведёт {score_diff} очк(а/ов) на {minute_display}."
    )
    
    bet_side = "П1" if leader_idx == 0 else "П2"
    repeat_prefix = "!повтор! " if match.get("is_repeat", False) else ""
    
    block = [
        f"{index}. {repeat_prefix}🏈 <b>{teams[0]}</b> - <b>{teams[1]}</b>",
        f"🏟️ {location}",
        f"📊 Счёт: {score} ({minute_display})",
        f"✅ Ставка: {bet_side} <b>{leader_name}</b>",
        f"🎯 {' '.join(analysis_parts)}",
        f"⚡ <b>ВЕРОЯТНОСТЬ: ~{probability}%</b>",
    ]
    
    odds_info = match.get("odds_info")
    if odds_info:
        odds_value = odds_info.value if hasattr(odds_info, "value") else odds_info.get("value") if isinstance(odds_info, dict) else None
        odds_corrected = match.get("odds_corrected")
        if odds_corrected:
            odds_value = odds_corrected
        if odds_value:
            odds_line = _format_odds_line(match, probability)
            if odds_line:
                block.append(odds_line)
    
    return "\n".join(block)


def _format_dota2_block(index: int, match: Dict) -> str:
    leader_idx = match["leader_index"]
    teams = match["teams"]
    leader_name = teams[leader_idx]
    maps_score = match.get("maps_score", "0:0")
    current_map_score = match.get("current_map_score", (0, 0))
    current_map = match.get("current_map", 1)
    game_time = match.get("game_time")
    tournament = match.get("tournament")
    country = match.get("country")
    location_parts = [part for part in (country, tournament) if part]
    location = " • ".join(location_parts) if location_parts else "—"
    
    probability = match.get("claude_probability") or _estimate_dota2_probability(match)
    match["estimated_probability"] = probability
    kills = match.get("kills")
    net_worth = match.get("net_worth") or match.get("gold")
    
    analysis_parts: List[str] = []
    maps_home, maps_away = maps_score.split(":") if ":" in maps_score else ("0", "0")
    maps_home_int = int(maps_home) if maps_home.isdigit() else 0
    maps_away_int = int(maps_away) if maps_away.isdigit() else 0
    
    # КРИТИЧЕСКОЕ: Анализируем ТЕКУЩУЮ КАРТУ, не весь матч
    import random
    control_variations = [
        f"<b>{leader_name}</b> контролирует",
        f"<b>{leader_name}</b> доминирует на",
        f"<b>{leader_name}</b> уверенно ведёт",
        f"<b>{leader_name}</b> превосходит соперника на",
        f"<b>{leader_name}</b> имеет явное преимущество на",
    ]
    control_phrase = random.choice(control_variations)
    analysis_parts.append(
        f"{control_phrase} {current_map} карту со счётом {current_map_score[0]}:{current_map_score[1]} по убийствам."
    )
    
    # Учитываем счет по картам как дополнительный фактор
    if maps_home_int != maps_away_int:
        analysis_parts.append(
            f"Счет по картам {maps_score} - команда играет сильно на каждой карте."
        )
    
    if kills:
        kills_diff = abs(kills[0] - kills[1])
        analysis_parts.append(f"Разница в убийствах: {kills_diff} (каждое убийство = 1000 монет).")
    
    if net_worth:
        net_worth_diff = net_worth[leader_idx] - net_worth[1 - leader_idx]
        if net_worth_diff > 0:
            analysis_parts.append(f"Преимущество по золоту: +{net_worth_diff:.0f} (Net Worth).")
        else:
            analysis_parts.append(f"⚠️ Отставание по золоту: {net_worth_diff:.0f} (слабая игра в лесу и фарме).")
    
    if game_time:
        analysis_parts.append(f"Время игры: {game_time} минут.")
    
    bet_side = "П1" if leader_idx == 0 else "П2"
    repeat_prefix = "!повтор! " if match.get("is_repeat", False) else ""
    
    block = [
        f"{index}. {repeat_prefix}🎮 <b>{teams[0]}</b> - <b>{teams[1]}</b>",
        f"🏟️ {location}",
        f"📊 Карты: {maps_score} | Текущая карта {current_map}: {current_map_score[0]}:{current_map_score[1]} по убийствам",
        f"✅ Ставка: {bet_side} <b>{leader_name}</b> (на победу в текущей карте)",
        f"🎯 {' '.join(analysis_parts)}",
        f"⚡ <b>ВЕРОЯТНОСТЬ: ~{probability}%</b>",
    ]
    
    odds_info = match.get("odds_info")
    if odds_info:
        odds_value = odds_info.value if hasattr(odds_info, "value") else odds_info.get("value") if isinstance(odds_info, dict) else None
        odds_corrected = match.get("odds_corrected")
        if odds_corrected:
            odds_value = odds_corrected
        if odds_value:
            odds_line = _format_odds_line(match, probability)
            if odds_line:
                block.append(odds_line)
    
    return "\n".join(block)


def _format_minute(value: Optional[str], status_code: Optional[str] = None) -> str:
    if value is not None:
        value_str = str(value).strip()
        if value_str and value_str.lower() not in {"none", "null"}:
            return value_str

    if status_code in {"7"}:
        return "перерыв"

    return "—"


def _format_match_block(index: int, match: Dict) -> str:
    leader_idx = match["leader_index"]
    teams = match["teams"]
    leader_name = teams[leader_idx]
    score = match["score"]
    minute = _format_minute(match.get("minute"), match.get("status_code"))
    # Формируем строку с минутой - если минута не определена, не показываем её
    minute_display = f"{minute}'" if minute and minute != "—" and minute != "?" else "live"
    
    tournament = match.get("tournament")
    country = match.get("country")
    location_parts = [part for part in (country, tournament) if part]
    location = " • ".join(location_parts) if location_parts else "—"

    probability = _estimate_probability(match)
    match["estimated_probability"] = probability

    has_xg = match.get("has_xg", False)
    possession_data = match.get("possession")
    if possession_data is None or not isinstance(possession_data, (tuple, list)) or len(possession_data) != 2:
        possession_home, possession_away = 50, 50
    else:
        possession_home, possession_away = possession_data
    shots_total_data = match.get("shots_total")
    has_shots_total = shots_total_data is not None and len(shots_total_data) == 2 and shots_total_data[0] is not None and shots_total_data[1] is not None
    shots_on_target = match.get("shots_on_target")
    if shots_on_target is None or not isinstance(shots_on_target, (tuple, list)) or len(shots_on_target) != 2:
        sot_home, sot_away = 0, 0
    else:
        sot_home, sot_away = shots_on_target

    bet_side = "П1" if leader_idx == 0 else "П2"

    # Сжимаем статистику в 1–2 строки
    stats_parts: List[str] = []
    if has_xg:
        xg_home, xg_away = match["xg"]
        stats_parts.append(f"xG {xg_home:.2f}-{xg_away:.2f}")
    shots_line = []
    if has_shots_total and shots_total_data is not None:
        shots_home, shots_away = shots_total_data
        shots_line.append(f"удары {int(round(shots_home))}-{int(round(shots_away))}")
    shots_line.append(f"створ {int(round(sot_home))}-{int(round(sot_away))}")
    stats_parts.append(", ".join(shots_line))
    stats_parts.append(
        f"владение {int(round(possession_home))}%–{int(round(possession_away))}%"
    )
    stats_compact = " • ".join(stats_parts)

    analysis = _format_analysis(match)

    # Убираем повторяющиеся фразы про коэффициент и xG — экономим длину сообщения

    # Добавляем анализ ИИ, если есть
    ai_note = ""
    if match.get("gpt_analysis_unavailable"):
        # GPT анализ недоступен - показываем предупреждение жирным шрифтом
        ai_note = f"\n<b>⚠️ GPT анализ недоступен. Используется внутренний алгоритм оценки.</b>"
    elif match.get("claude_probability"):
        ai_prob = match.get("claude_probability")
        ai_rec = match.get("claude_recommendation", "")
        ai_source = match.get("ai_source", "unknown")
        
        # Определяем название ИИ для отображения
        if "gpt" in ai_source.lower() or "aitunnel_gpt" in ai_source.lower():
            ai_name = "CHAT GPT AI"
        elif "claude" in ai_source.lower():
            ai_name = "Claude AI"  # На случай, если в будущем включим
        else:
            ai_name = "ИИ"
        
        if ai_rec:
            ai_note = f"\n🤖 {ai_name}: {ai_rec}"
        # Используем вероятность от ИИ, если она есть
        if ai_prob and ai_prob > 0:
            probability = ai_prob
    
    # Добавляем пометку "!повтор!" если матч уже был отправлен
    repeat_prefix = "!повтор! " if match.get("is_repeat", False) else ""
    
    # Добавляем информацию о коэффициенте и Expected Value
    odds_info = match.get("odds_info")
    odds_display = ""
    ev_display = ""
    if odds_info:
        odds_value = None
        if hasattr(odds_info, "value"):
            odds_value = odds_info.value
        elif isinstance(odds_info, dict):
            odds_value = odds_info.get("value")
        
        # Используем скорректированный коэффициент для отображения
        odds_corrected = match.get("odds_corrected")
        if odds_corrected:
            odds_value = odds_corrected
        
        if odds_value:
            odds_display = f"💰 Коэффициент: {odds_value:.2f}"
            
            # Рассчитываем Expected Value
            try:
                from roi_optimizer import calculate_expected_value
                ev = calculate_expected_value(probability, odds_value)
                if ev >= 0:
                    ev_display = f" | EV: +{ev*100:.1f}%"
                else:
                    ev_display = f" | EV: {ev*100:.1f}%"
            except ImportError:
                pass
    
    # Формируем строку с минутой - если минута не определена, не показываем её
    minute_display = f"{minute}'" if minute and minute != "—" and minute != "?" else "live"
    
    block = [
        f"{index}. {repeat_prefix}🎯 <b>{teams[0]}</b> - <b>{teams[1]}</b>",
        f"🏟️ {location}",
        f"📊 Счет: {score} ({minute_display}) • {bet_side} <b>{leader_name}</b>",
        f"📈 {stats_compact}",
        f"🎯 {analysis}{ai_note}",
        f"⚡ <b>ВЕРОЯТНОСТЬ: ~{probability}%</b>{odds_display}{ev_display}",
    ]
    return "\n".join(block)


def _safe_metric_value(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return float(value)


def _estimate_basketball_probability(match: Dict) -> int:
    leader = match["leader_metrics"]
    trailing = match["trailing_metrics"]

    def _diff(metric: str, multiplier: float = 1.0) -> float:
        leader_value = _safe_metric_value(leader.get(metric))
        trailing_value = _safe_metric_value(trailing.get(metric))
        if leader_value is None or trailing_value is None:
            return 0.0
        return max(0.0, (leader_value - trailing_value) * multiplier)

    score_gap = abs(match["home_score"] - match["away_score"])
    minute_numeric = match.get("minute_numeric") or 0
    time_factor = min(1.0, max(0.2, minute_numeric / 40.0))
    dominance = match.get("dominance_score", 0.0)

    prob_floor = int(round(getattr(TUNING_SETTINGS, "basketball_probability_floor", PROBABILITY_MIN / 100) * 100))
    prob_cap = int(round(getattr(TUNING_SETTINGS, "basketball_probability_cap", PROBABILITY_MAX / 100) * 100))

    probability = (
        60
        + score_gap * 1.0
        + _diff("points", 0.25)
        + _diff("rebounds", 0.8)
        + _diff("assists", 0.6)
        + _diff("field_goal_pct", 5.0)
        + dominance * 0.8
        + time_factor * 10
    )
    probability = max(prob_floor, min(prob_cap, probability))
    return int(round(probability))


def _format_basketball_block(index: int, match: Dict) -> str:
    leader_idx = match["leader_index"]
    trailing_idx = 1 - leader_idx
    teams = match["teams"]
    leader_name = teams[leader_idx]
    trailing_name = teams[trailing_idx]
    score = match["score"]
    minute = _format_minute(match.get("minute"), match.get("status_code"))
    # Формируем строку с минутой - если минута не определена, не показываем её
    minute_display = f"{minute}'" if minute and minute != "—" and minute != "?" else "live"
    
    tournament = match.get("tournament")
    country = match.get("country")
    location_parts = [part for part in (country, tournament) if part]
    location = " • ".join(location_parts) if location_parts else "—"

    def _fmt(value: Optional[float]) -> str:
        safe_value = _safe_metric_value(value)
        if safe_value is None:
            return "—"
        return str(int(round(safe_value)))

    leader = match["leader_metrics"]
    trailing = match["trailing_metrics"]

    stats_lines = [
        f"* Очки: {_fmt(leader.get('points'))} - {_fmt(trailing.get('points'))}",
        f"* Подборы: {_fmt(leader.get('rebounds'))} - {_fmt(trailing.get('rebounds'))}",
        f"* Передачи: {_fmt(leader.get('assists'))} - {_fmt(trailing.get('assists'))}",
    ]
    fg_leader = _safe_metric_value(leader.get("field_goal_pct"))
    fg_trailing = _safe_metric_value(trailing.get("field_goal_pct"))
    if fg_leader is not None and fg_trailing is not None:
        stats_lines.append(
            f"* Процент попаданий: {fg_leader:.1f} - {fg_trailing:.1f}"
        )
    stats_block = "\n".join(stats_lines)

    analysis_parts = []
    points_leader = _safe_metric_value(leader.get("points"))
    points_trailing = _safe_metric_value(trailing.get("points"))
    if points_leader is not None and points_trailing is not None:
        diff = points_leader - points_trailing
        if diff >= 6:
            analysis_parts.append(
                f"по очкам {int(round(points_leader))}-{int(round(points_trailing))}"
            )

    rebounds_leader = _safe_metric_value(leader.get("rebounds"))
    rebounds_trailing = _safe_metric_value(trailing.get("rebounds"))
    if rebounds_leader is not None and rebounds_trailing is not None:
        rebounds_diff = rebounds_leader - rebounds_trailing
        if rebounds_diff >= 3:
            analysis_parts.append("по подборам")

    assists_leader = _safe_metric_value(leader.get("assists"))
    assists_trailing = _safe_metric_value(trailing.get("assists"))
    if assists_leader is not None and assists_trailing is not None:
        assists_diff = assists_leader - assists_trailing
        if assists_diff >= 2:
            analysis_parts.append("по передачам")

    if not analysis_parts:
        analysis_parts.append("по ходу матча")

    import random
    
    # Вариации фразы о контроле игры
    control_phrase = _get_control_phrase_variation(leader_name, "game")
    analysis = (
        f"{control_phrase} — ведет {score} на {minute}' {', '.join(analysis_parts)}. "
        f"<b>{trailing_name}</b> пока уступает по качеству моментов."
    )

    if match.get("odds_tier") == "extended":
        analysis += " Коэффициент выше базового диапазона — контролируем размер ставки."

    probability = _estimate_basketball_probability(match)
    match["estimated_probability"] = probability

    # Добавляем анализ ИИ, если есть
    ai_note = ""
    if match.get("gpt_analysis_unavailable"):
        # GPT анализ недоступен - показываем предупреждение жирным шрифтом
        ai_note = f"\n<b>⚠️ GPT анализ недоступен. Используется внутренний алгоритм оценки.</b>"
    elif match.get("claude_probability"):
        ai_prob = match.get("claude_probability")
        ai_rec = match.get("claude_recommendation", "")
        ai_source = match.get("ai_source", "unknown")
        
        # Определяем название ИИ для отображения
        if "gpt" in ai_source.lower() or "aitunnel_gpt" in ai_source.lower():
            ai_name = "CHAT GPT AI"
        elif "claude" in ai_source.lower():
            ai_name = "Claude AI"  # На случай, если в будущем включим
        else:
            ai_name = "ИИ"
        
        if ai_rec:
            ai_note = f"\n🤖 {ai_name}: {ai_rec}"
        # Используем вероятность от ИИ, если она есть
        if ai_prob and ai_prob > 0:
            probability = ai_prob
    
    # Добавляем пометку "!повтор!" если матч уже был отправлен
    repeat_prefix = "!повтор! " if match.get("is_repeat", False) else ""
    
    # Добавляем информацию о коэффициенте и Expected Value
    odds_info = match.get("odds_info")
    odds_display = ""
    ev_display = ""
    if odds_info:
        odds_value = None
        if hasattr(odds_info, "value"):
            odds_value = odds_info.value
        elif isinstance(odds_info, dict):
            odds_value = odds_info.get("value")
        
        # Используем скорректированный коэффициент для отображения
        odds_corrected = match.get("odds_corrected")
        if odds_corrected:
            odds_value = odds_corrected
        
        if odds_value:
            odds_display = f"💰 Коэффициент: {odds_value:.2f}"
            
            # Рассчитываем Expected Value
            try:
                from roi_optimizer import calculate_expected_value
                ev = calculate_expected_value(probability, odds_value)
                if ev >= 0:
                    ev_display = f" | EV: +{ev*100:.1f}%"
                else:
                    ev_display = f" | EV: {ev*100:.1f}%"
            except ImportError:
                pass
    
    block_lines = [
        f"{index}. {repeat_prefix}🏀 <b>{teams[0]}</b> - <b>{teams[1]}</b>",
        f"🏟️ {location}",
        f"📊 Счет: {score} ({minute_display})",
        f"✅ Ставка: {'П1' if leader_idx == 0 else 'П2'} <b>{leader_name}</b>",
        "",
        "📈 РЕАЛЬНАЯ СТАТИСТИКА:",
        stats_block,
        "",
        f"🎯 АНАЛИЗ:\n{analysis}{ai_note}",
        "",
        f"⚡ <b>ВЕРОЯТНОСТЬ: ~{probability}%</b>{odds_display}{ev_display}",
    ]
    return "\n".join(block_lines)


def _get_recent_slugs(hours: float = 4) -> set[str]:
    """Получает список slug матчей, отправленных за последние N часов (поддерживает дробные значения, например 0.5 = 30 минут)."""
    log_file = Path("data/recommendations_log.csv")
    if not log_file.exists():
        return set()
    
    now = datetime.now(ZoneInfo("Europe/Moscow"))
    cutoff = now - timedelta(hours=hours)
    recent_slugs = set()
    
    try:
        with log_file.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamp_str = row.get("timestamp_msk", "")
                if not timestamp_str:
                    continue
                try:
                    row_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    row_time = row_time.replace(tzinfo=ZoneInfo("Europe/Moscow"))
                    if row_time >= cutoff:
                        slug = row.get("slug", "").strip()
                        if slug:
                            recent_slugs.add(slug)
                except (ValueError, TypeError):
                    continue
    except Exception:
        pass
    
    return recent_slugs


def _filter_duplicates(matches: List[Dict], recent_slugs: set[str], filter_repeats: bool = True) -> List[Dict]:
    """
    Обрабатывает матчи, которые уже были отправлены недавно.
    
    Args:
        matches: Список матчей
        recent_slugs: Множество slug матчей, отправленных недавно
        filter_repeats: Если True - полностью фильтрует повторные матчи (рекомендуется)
                       Если False - помечает как повтор (для показа в конце)
    
    Returns:
        Отфильтрованный или помеченный список матчей
    """
    if filter_repeats:
        # КРИТИЧЕСКОЕ: Полностью фильтруем повторные матчи
        # Причина: при повторной публикации к-ты уже низкие или ставки недоступны
        filtered = []
        filtered_count = 0
        for match in matches:
            slug = match.get("slug", "").strip()
            if slug and slug in recent_slugs:
                filtered_count += 1
                if filtered_count <= 3:  # Показываем первые 3 отфильтрованных
                    log_debug(f"Filtered repeat match: {slug} (коэффициенты уже низкие или ставка недоступна)")
            else:
                match["is_repeat"] = False
                filtered.append(match)
        if filtered_count > 3:
            log_debug(f"... and {filtered_count - 3} more repeat matches filtered")
        if filtered_count > 0:
            log_info(f"Filtered {filtered_count} repeat matches (not publishing - odds likely too low or bet unavailable)")
        return filtered
    else:
        # Помечаем как повтор (для показа в конце сообщения)
        marked_count = 0
        for match in matches:
            slug = match.get("slug", "").strip()
            if slug and slug in recent_slugs:
                match["is_repeat"] = True
                marked_count += 1
                if marked_count <= 3:  # Показываем первые 3 помеченных
                    log_debug(f"Marked as repeat match: {slug}")
            else:
                match["is_repeat"] = False
        if marked_count > 3:
            log_debug(f"... and {marked_count - 3} more matches marked as repeats")
        return matches  # Возвращаем все матчи, не фильтруем


def generate_live_report(
    max_matches: int = 3
) -> Tuple[str, List[Dict], Dict[str, Any]]:
    now = datetime.now(ZoneInfo("Europe/Moscow"))
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%d.%m.%Y")
    context: Dict[str, Any] = {
        "generated_at": now,
        "time_str": time_str,
        "date_str": date_str,
    }
    
    # Получаем список недавно отправленных матчей
    # Окно дедупликации: 1 час (чтобы матчи не повторялись слишком часто)
    recent_slugs = _get_recent_slugs(hours=1.0)  # 1 час

    # ПАРАЛЛЕЛЬНЫЙ СБОР МАТЧЕЙ для ускорения прогона
    # Вместо последовательного сбора (футбол → теннис → баскетбол), собираем все параллельно
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    log_info("Starting parallel match collection for all sports...")
    football_matches = []
    tennis_matches = []
    basketball_matches = []
    volleyball_matches = []
    american_football_matches = []
    dota2_matches = []
    
    def collect_football():
        try:
            return _select_top_matches(limit=max_matches * 2)
        except Exception as e:
            log_warning(f"Error collecting football matches: {e}")
            return []
    
    def collect_tennis():
        try:
            return _select_top_tennis_matches(limit=max_matches * 2)
        except Exception as e:
            log_warning(f"Error collecting tennis matches: {e}")
            return []
    
    def collect_basketball():
        try:
            return _select_top_basketball_matches(limit=max_matches * 2)
        except Exception as e:
            log_warning(f"Error collecting basketball matches: {e}")
            return []
    
    def collect_volleyball():
        try:
            return _select_top_volleyball_matches(limit=max_matches * 2)
        except Exception as e:
            log_warning(f"Error collecting volleyball matches: {e}")
            return []
    
    def collect_american_football():
        try:
            return _select_top_american_football_matches(limit=max_matches * 2)
        except Exception as e:
            log_warning(f"Error collecting american football matches: {e}")
            return []
    
    def collect_dota2():
        try:
            return _select_top_dota2_matches(limit=max_matches * 2)
        except Exception as e:
            log_warning(f"Error collecting dota2 matches: {e}")
            return []
    
    # Запускаем параллельный сбор
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(collect_football): "football",
            executor.submit(collect_tennis): "tennis",
            executor.submit(collect_basketball): "basketball",
            executor.submit(collect_volleyball): "volleyball",
            executor.submit(collect_american_football): "american_football",
            executor.submit(collect_dota2): "dota2",
        }
        
        for future in as_completed(futures):
            sport = futures[future]
            try:
                matches = future.result()
                if sport == "football":
                    football_matches = matches
                elif sport == "tennis":
                    tennis_matches = matches
                elif sport == "basketball":
                    basketball_matches = matches
                elif sport == "volleyball":
                    volleyball_matches = matches
                elif sport == "american_football":
                    american_football_matches = matches
                elif sport == "dota2":
                    dota2_matches = matches
                log_info(f"Collected {len(matches)} {sport} matches")
            except Exception as e:
                log_error(f"Error getting {sport} matches: {e}")
    
    # Теперь распределяем слоты по приоритету: футбол → теннис → баскетбол → волейбол → американский футбол → Dota 2
    selected_football = football_matches[:max_matches]
    remaining_slots = max(0, max_matches - len(selected_football))
    
    selected_tennis = []
    if remaining_slots > 0:
        selected_tennis = tennis_matches[:remaining_slots]
        remaining_slots = max(0, remaining_slots - len(selected_tennis))
    
    selected_basketball = []
    if remaining_slots > 0:
        selected_basketball = basketball_matches[:remaining_slots]
        remaining_slots = max(0, remaining_slots - len(selected_basketball))
    
    selected_volleyball = []
    if remaining_slots > 0:
        selected_volleyball = volleyball_matches[:remaining_slots]
        remaining_slots = max(0, remaining_slots - len(selected_volleyball))
    
    selected_american_football = []
    if remaining_slots > 0:
        selected_american_football = american_football_matches[:remaining_slots]
        remaining_slots = max(0, remaining_slots - len(selected_american_football))
    
    selected_dota2 = []
    if remaining_slots > 0:
        selected_dota2 = dota2_matches[:remaining_slots]

    selected_matches = (selected_football + selected_tennis + selected_basketball + 
                       selected_volleyball + selected_american_football + selected_dota2)
    
    # Логируем количество матчей до дедупликации
    matches_before_dedup = len(selected_matches)
    if matches_before_dedup > 0:
        log_debug(f"Found {matches_before_dedup} matches before deduplication")
        log_debug(f"Recent slugs in deduplication window: {len(recent_slugs)}")
    
    # КРИТИЧЕСКОЕ: Фильтруем или помечаем дубликаты (матчи, которые уже были отправлены)
    # По умолчанию фильтруем полностью, т.к. при повторной публикации к-ты уже низкие или ставки недоступны
    filter_repeats = getattr(TUNING_SETTINGS, "filter_repeat_matches", True)
    selected_matches = _filter_duplicates(selected_matches, recent_slugs, filter_repeats=filter_repeats)
    
    if not filter_repeats:
        marked_as_repeat = sum(1 for m in selected_matches if m.get("is_repeat", False))
        if marked_as_repeat > 0:
            log_debug(f"Marked {marked_as_repeat} matches as repeats (will show with !повтор! prefix at the end)")
    
    # КРИТИЧЕСКОЕ ТРЕБОВАНИЕ: Используем GPT для анализа КАЖДОГО матча
    # Это важно для качества и привлекательности канала
    if selected_matches:
        try:
            from ai_analyzer import analyze_matches_batch
            
            log_info(f"🤖 Starting AI analysis (GPT) on {len(selected_matches)} filtered matches...")
            
            # Группируем матчи по видам спорта
            matches_by_sport = {}
            for match in selected_matches:
                sport_type = match.get("sport_type", "football")
                if sport_type not in matches_by_sport:
                    matches_by_sport[sport_type] = []
                matches_by_sport[sport_type].append(match)
            
            # Логируем распределение по видам спорта
            for sport_type, sport_matches in matches_by_sport.items():
                log_info(f"📊 {sport_type}: {len(sport_matches)} matches ready for AI analysis")
            
            all_analyzed_matches = []
            matches_to_remove = []
            analyzed_slugs = set()  # Отслеживаем slugs матчей, которые прошли через GPT анализ
            
            for sport_type, sport_matches in matches_by_sport.items():
                # КРИТИЧЕСКОЕ: Анализируем КАЖДЫЙ матч через GPT
                # Используется GPT через AITunnel
                log_info(f"🔄 Processing {len(sport_matches)} {sport_type} matches through AI...")
                try:
                    analyzed = analyze_matches_batch(sport_matches, sport_type)
                    log_info(f"✅ AI analysis returned {len(analyzed)}/{len(sport_matches)} {sport_type} matches")
                    
                    # Детальное логирование: сколько матчей с успешным GPT анализом
                    successful_count = len([m for m in analyzed if m.get("claude_probability")])
                    unavailable_count = len([m for m in analyzed if m.get("gpt_analysis_unavailable")])
                    log_info(f"   └─ Успешно проанализировано: {successful_count}, Недоступно: {unavailable_count}")
                except Exception as batch_error:
                    log_error(f"🚨 КРИТИЧЕСКАЯ ОШИБКА при вызове analyze_matches_batch для {sport_type}: {batch_error}")
                    import traceback
                    log_error(f"🚨 Traceback:\n{traceback.format_exc()}")
                    # Если analyze_matches_batch упал с ошибкой, помечаем все матчи как недоступные
                    analyzed = []
                    for match in sport_matches:
                        match["gpt_analysis_unavailable"] = True
                        match["gpt_unavailable_reason"] = f"analyze_matches_batch failed: {str(batch_error)}"
                        analyzed.append(match)
                    log_warning(f"⚠️ Все {len(sport_matches)} {sport_type} матчей помечены как недоступные для GPT анализа")
                
                # КРИТИЧЕСКАЯ ПРОВЕРКА: Убеждаемся, что ВСЕ отправленные матчи вернулись
                if len(analyzed) != len(sport_matches):
                    log_error(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: Для {sport_type} отправлено {len(sport_matches)} матчей, но вернулось {len(analyzed)}!")
                    # Находим матчи, которые не вернулись
                    sent_slugs = {m.get("slug") for m in sport_matches if m.get("slug")}
                    returned_slugs = {m.get("slug") for m in analyzed if m.get("slug")}
                    missing_slugs = sent_slugs - returned_slugs
                    if missing_slugs:
                        log_error(f"🚨 Пропущенные матчи: {missing_slugs}")
                
                for match in analyzed:
                    # Отслеживаем, какие матчи прошли через GPT анализ
                    slug = match.get("slug")
                    if slug:
                        analyzed_slugs.add(slug)
                    ai_source = match.get("ai_source", "unknown")
                    teams = match.get("teams", ["?", "?"])
                    teams_str = f"{teams[0]} vs {teams[1]}"
                    
                    # КРИТИЧЕСКОЕ: Если GPT явно пишет "НЕ РЕКОМЕНДУЕТСЯ" - матч НЕ публикуется
                    # Это строгая фильтрация - никаких исключений
                    probability = match.get("claude_probability", 0)
                    recommended = match.get("claude_recommended", True)
                    
                    # Подробное логирование причин исключения
                    exclusion_reason = None
                    exclusion_details = []
                    
                    # КРИТИЧЕСКАЯ ПРОВЕРКА: Проверяем и recommended, и текст рекомендации на различные варианты формулировок
                    recommendation_text = match.get("claude_recommendation", "")
                    recommendation_upper = str(recommendation_text).upper()
                    
                    # Расширенный список паттернов для проверки "не рекомендуется"
                    not_recommended_patterns = [
                        "НЕ РЕКОМЕНДУЕТСЯ",
                        "НЕ РЕКОМЕНДУЮ",
                        "НЕ РЕКОМЕНДОВАТЬ",
                        "НЕ СТОИТ",
                        "НЕ СОВЕТУЮ",
                        "НЕ СОВЕТУЕТСЯ",
                        "НЕ ПОДХОДИТ",
                        "НЕ ПОДХОДИТ ДЛЯ СТАВКИ",
                        "НЕ ПОДХОДИТ ДЛЯ РЕКОМЕНДАЦИИ",
                    ]
                    
                    has_not_recommended = any(pattern in recommendation_upper for pattern in not_recommended_patterns)
                    
                    if not recommended or has_not_recommended:
                        exclusion_reason = "GPT НЕ РЕКОМЕНДУЕТ"
                        exclusion_details.append(f"claude_recommended={recommended}")
                        if has_not_recommended:
                            found_pattern = next((p for p in not_recommended_patterns if p in recommendation_upper), "НЕ РЕКОМЕНДУЕТСЯ")
                            exclusion_details.append(f"текст содержит '{found_pattern}'")
                        prob = match.get("claude_probability", "?")
                        exclusion_details.append(f"вероятность={prob}%")
                        
                        # Дополнительная информация о матче для диагностики
                        sport = match.get("sport_type", "?")
                        minute = match.get("minute_numeric", "?")
                        dominance = match.get("dominance_score", "?")
                        exclusion_details.append(f"спорт={sport}, минута={minute}, dominance={dominance}")
                        
                        log_warning(f"🚫 ИСКЛЮЧЕН: {teams_str} | Причина: {exclusion_reason} | Детали: {', '.join(exclusion_details)}")
                        matches_to_remove.append(match)
                        continue  # Пропускаем дальнейшую обработку
                    elif probability > 0 and (probability < 65 or probability > 90):
                        # Ужесточенный диапазон: 65-90% (как указано в промпте GPT)
                        # Исключаем матчи вне этого диапазона
                        exclusion_reason = "ВЕРОЯТНОСТЬ ВНЕ ДИАПАЗОНА 65-90%"
                        exclusion_details.append(f"вероятность={probability}%")
                        exclusion_details.append(f"диапазон=65-90%")
                        
                        # Дополнительная информация о матче для диагностики
                        sport = match.get("sport_type", "?")
                        minute = match.get("minute_numeric", "?")
                        dominance = match.get("dominance_score", "?")
                        exclusion_details.append(f"спорт={sport}, минута={minute}, dominance={dominance}")
                        
                        log_warning(f"🚫 ИСКЛЮЧЕН: {teams_str} | Причина: {exclusion_reason} | Детали: {', '.join(exclusion_details)}")
                        matches_to_remove.append(match)
                    else:
                        all_analyzed_matches.append(match)
                        if match.get("claude_probability"):
                            factors = match.get("claude_factors", [])
                            factors_str = ", ".join(factors[:3]) if factors else "на основе анализа"
                            log_info(f"✅ ПРОШЕЛ: {teams_str} | {ai_source.upper()} | Вероятность: {match.get('claude_probability')}% | Факторы: {factors_str}")
            
            # КРИТИЧЕСКОЕ: Дополнительная проверка - удаляем матчи с "НЕ РЕКОМЕНДУЕТСЯ" из all_analyzed_matches
            # Это защита на случай, если матч каким-то образом попал в all_analyzed_matches
            final_matches = []
            excluded_by_recommendation = 0
            excluded_by_probability = 0
            
            for match in all_analyzed_matches:
                recommended = match.get("claude_recommended", True)
                probability = match.get("claude_probability", 0)
                recommendation_text = match.get("claude_recommendation", "")
                teams = match.get("teams", ["?", "?"])
                teams_str = f"{teams[0]} vs {teams[1]}" if isinstance(teams, list) else str(teams)
                slug = match.get("slug", "?")
                
                # КРИТИЧЕСКАЯ ПРОВЕРКА: Если GPT явно написал "НЕ РЕКОМЕНДУЕТСЯ" - матч НЕ публикуется
                # Проверяем не только флаг recommended, но и текст рекомендации на различные варианты формулировок
                recommendation_upper = str(recommendation_text).upper()
                not_recommended_patterns = [
                    "НЕ РЕКОМЕНДУЕТСЯ",
                    "НЕ РЕКОМЕНДУЮ",
                    "НЕ РЕКОМЕНДОВАТЬ",
                    "НЕ СТОИТ",
                    "НЕ СОВЕТУЮ",
                    "НЕ СОВЕТУЕТСЯ",
                    "НЕ ПОДХОДИТ",
                    "НЕ ПОДХОДИТ ДЛЯ СТАВКИ",
                    "НЕ ПОДХОДИТ ДЛЯ РЕКОМЕНДАЦИИ",
                ]
                
                has_not_recommended = any(pattern in recommendation_upper for pattern in not_recommended_patterns)
                
                if not recommended or has_not_recommended:
                    excluded_by_recommendation += 1
                    reason = "флаг claude_recommended=False" if not recommended else f"текст содержит '{next((p for p in not_recommended_patterns if p in recommendation_upper), 'НЕ РЕКОМЕНДУЕТСЯ')}'"
                    log_warning(f"🚫 КРИТИЧНО: Исключаем матч {teams_str} ({slug}) - GPT НЕ РЕКОМЕНДУЕТ (причина: {reason})")
                    continue
                
                # Проверка диапазона вероятности
                if probability > 0 and (probability < 65 or probability > 90):
                    excluded_by_probability += 1
                    log_debug(f"  ❌ {teams_str} ({slug}): Вероятность {probability}% вне диапазона 65-90%")
                    continue
                
                # Матч прошел все проверки
                final_matches.append(match)
            
            # КРИТИЧЕСКАЯ ПРОВЕРКА: Убеждаемся, что ВСЕ матчи из selected_matches были отправлены на GPT анализ
            # Создаем словарь всех отправленных матчей по slug
            all_sent_slugs = set()
            for sport_type, sport_matches in matches_by_sport.items():
                for match in sport_matches:
                    slug = match.get("slug")
                    if slug:
                        all_sent_slugs.add(slug)
            
            # Проверяем, что все матчи из selected_matches были отправлены на анализ
            missing_matches = []
            for match in selected_matches:
                slug = match.get("slug")
                if slug and slug not in all_sent_slugs:
                    teams = match.get("teams", ["?", "?"])
                    teams_str = f"{teams[0]} vs {teams[1]}" if isinstance(teams, list) else str(teams)
                    log_error(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: Матч {teams_str} ({slug}) НЕ был отправлен на GPT анализ!")
                    missing_matches.append(match)
            
            if missing_matches:
                log_error(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: {len(missing_matches)} матчей НЕ были отправлены на GPT анализ!")
                # Помечаем пропущенные матчи как недоступные для анализа
                for match in missing_matches:
                    match["gpt_analysis_unavailable"] = True
                    match["gpt_unavailable_reason"] = "Match was not sent to GPT analysis (critical error)"
            
            # КРИТИЧЕСКАЯ ПРОВЕРКА: Убеждаемся, что все отправленные матчи вернулись из анализа
            # Если матч был отправлен, но не вернулся - это ошибка
            for sport_type, sport_matches in matches_by_sport.items():
                for match in sport_matches:
                    slug = match.get("slug")
                    if slug and slug not in analyzed_slugs:
                        # Матч был отправлен на анализ, но GPT его не вернул
                        # Это критическая ошибка - матч должен был вернуться (даже с флагом gpt_analysis_unavailable)
                        teams = match.get("teams", ["?", "?"])
                        teams_str = f"{teams[0]} vs {teams[1]}" if isinstance(teams, list) else str(teams)
                        log_error(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: Матч {teams_str} ({slug}) был отправлен на GPT анализ, но НЕ вернулся в результатах!")
            
            # Обновляем selected_matches только проверенными матчами
            selected_matches = final_matches
            
            ai_analyzed_count = len([m for m in selected_matches if m.get("claude_probability")])
            ai_sources = set(m.get("ai_source", "unknown") for m in selected_matches if m.get("claude_probability"))
            unavailable_count = len([m for m in selected_matches if m.get("gpt_analysis_unavailable")])
            
            log_info(f"📊 GPT analysis completed: {ai_analyzed_count} matches passed, {len(matches_to_remove)} excluded")
            if len(matches_to_remove) > 0:
                log_info(f"   └─ Исключено по причине 'GPT не рекомендует': {excluded_by_recommendation}")
                log_info(f"   └─ Исключено по причине 'Вероятность вне 65-90%': {excluded_by_probability}")
            log_info(f"   └─ AI источники: {', '.join(ai_sources) if ai_sources else 'none'}")
            
            # Детальное логирование матчей с недоступным GPT анализом
            if unavailable_count > 0:
                log_warning(f"⚠️ ВНИМАНИЕ: {unavailable_count} матчей будут опубликованы с предупреждением 'GPT анализ недоступен'")
                for match in selected_matches:
                    if match.get("gpt_analysis_unavailable"):
                        teams = match.get("teams", ["?", "?"])
                        teams_str = f"{teams[0]} vs {teams[1]}" if isinstance(teams, list) else str(teams)
                        reason = match.get("gpt_unavailable_reason", "unknown")
                        log_warning(f"   └─ {teams_str}: {reason}")
                
        except ImportError as import_err:
            log_error(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: Не удалось импортировать ai_analyzer: {import_err}")
            log_error(f"🚨 Детали ошибки импорта: {type(import_err).__name__}: {import_err}")
            import traceback
            log_error(f"🚨 Traceback:\n{traceback.format_exc()}")
            # Помечаем все матчи, что GPT анализ не был выполнен
            for match in selected_matches:
                match["gpt_analysis_unavailable"] = True
                match["gpt_unavailable_reason"] = f"ImportError: {str(import_err)}"
        except Exception as e:
            log_error(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: Ошибка при выполнении GPT анализа: {e}")
            log_error(f"🚨 Тип ошибки: {type(e).__name__}")
            import traceback
            log_error(f"🚨 Traceback:\n{traceback.format_exc()}")
            # Помечаем все матчи, что GPT анализ не был выполнен
            for match in selected_matches:
                match["gpt_analysis_unavailable"] = True
                match["gpt_unavailable_reason"] = f"Exception: {type(e).__name__}: {str(e)}"
    
    # КРИТИЧЕСКАЯ ПРОВЕРКА: Исключаем матчи, которые не прошли через GPT анализ
    # Если матч не имеет claude_probability И не помечен как gpt_analysis_unavailable,
    # значит GPT анализ не был выполнен, и такой матч НЕ должен публиковаться
    # Эта проверка выполняется ТОЛЬКО если selected_matches не пустой
    if selected_matches:
        matches_without_gpt = []
        final_selected_matches = []
        
        for match in selected_matches:
            has_gpt_probability = match.get("claude_probability") is not None and match.get("claude_probability") > 0
            has_gpt_unavailable_flag = match.get("gpt_analysis_unavailable", False)
            
            if not has_gpt_probability and not has_gpt_unavailable_flag:
                # Матч не прошел через GPT анализ и не помечен как недоступный
                # Это означает, что GPT анализ не был выполнен для этого матча
                teams = match.get("teams", ["?", "?"])
                teams_str = f"{teams[0]} vs {teams[1]}" if isinstance(teams, list) else str(teams)
                slug = match.get("slug", "?")
                matches_without_gpt.append(match)
                log_warning(f"🚫 КРИТИЧНО: Исключаем матч {teams_str} ({slug}) - GPT анализ НЕ был выполнен (нет claude_probability и нет флага gpt_analysis_unavailable)")
            else:
                # Матч либо прошел GPT анализ, либо помечен как недоступный (будет опубликован с предупреждением)
                final_selected_matches.append(match)
        
        if matches_without_gpt:
            log_warning(f"⚠️ Исключено {len(matches_without_gpt)} матчей без GPT анализа")
        
        # Обновляем selected_matches только матчами, которые прошли GPT анализ или помечены как недоступный
        selected_matches = final_selected_matches
    
    # Логируем количество матчей после дедупликации (теперь не фильтруем, а помечаем)
    matches_after_dedup = len(selected_matches)
    if matches_before_dedup > 0:
        repeat_count = sum(1 for m in selected_matches if m.get("is_repeat", False))
        log_debug(f"After deduplication marking: {matches_after_dedup} matches ({repeat_count} marked as repeats)")
        # Показываем slugs оставшихся матчей для отладки
        if matches_after_dedup > 0:
            remaining_slugs = [m.get("slug", "?") for m in selected_matches]
            log_debug(f"Remaining slugs: {remaining_slugs}")
    
    # ГИБРИДНЫЙ ПОДХОД: НЕ фильтруем по коэффициентам и EV
    # Мы делаем качественный анализ, а оценку коэффициентов оставляем подписчикам
    # Показываем рекомендуемый коэффициент, но не исключаем матчи на его основе
    
    # НОВЫЙ ПОДХОД: Приоритизируем по качеству анализа (вероятность, dominance), а не по коэффициентам
    # Это позволяет показывать лучшие матчи по статистике, независимо от коэффициентов
    if len(selected_matches) > max_matches:
        # Сортируем по:
        # 1. Вероятности (выше = лучше)
        # 2. Dominance (выше = лучше)
        # 3. Времени матча (позже = лучше, т.к. меньше времени для отыгрыша)
        selected_matches.sort(key=lambda m: (
            -(m.get("claude_probability") or m.get("estimated_probability", 0)),  # Вероятность
            -(m.get("dominance_score", 0)),  # Dominance
            -(m.get("minute_numeric", 0))  # Время матча (позже = лучше)
        ), reverse=False)  # reverse=False потому что отрицательные значения уже инвертированы
        selected_matches = selected_matches[:max_matches]

    if not selected_matches:
        # Чередуем два типа сообщений когда нет матчей
        # Используем время для детерминированного чередования
        use_detailed = (now.hour * 60 + now.minute) % 40 < 20  # Чередуем каждые 20 минут
        
        # Импортируем трекер для отслеживания подряд идущих "нет матчей"
        from no_matches_tracker import increment_no_matches_count, get_consecutive_no_matches_count
        from no_matches_messages import get_no_matches_message_by_count
        
        if use_detailed:
            # Красивое детальное сообщение
            discipline_tips = [
                "📊 Поддерживай дисциплину банка: те же 2% на сигнал, без догонов.",
                "💡 Напоминание: не рискуйте более 2% банка на одну ставку.",
                "⏱️ Без суеты. Всё успеем — сначала смотрим цифры, потом ставим.",
                "🔍 Наши сигналы — только по проверенной статистике. Ставим не сердцем, а цифрами.",
                "📈 Спокойные ставки — залог долгосрочного успеха. Не торопимся.",
                "🎯 Дисциплина важнее азарта. Следуем системе, не эмоциям.",
                "💪 Терпение и выдержка — ключ к стабильной прибыли.",
                "📊 Отслеживай результаты: дата, матч, коэффициент и чем всё закончилось.",
                "🗂️ Любая ставка — зафиксируй купон или скрин: потом легче считать реальный профит.",
                "⚖️ Баланс — основа успеха. Не увеличивай ставки после проигрыша.",
            ]
            
            # Получаем специальное сообщение в зависимости от количества подряд идущих "нет матчей"
            consecutive_count = increment_no_matches_count()
            if consecutive_count >= 3:
                # Используем специальные успокаивающие сообщения
                no_matches_text = get_no_matches_message_by_count(consecutive_count)
            else:
                # Обычное сообщение для первых 1-2 раз
                no_matches_text = "Сейчас подходящих матчей в топ-лигах нет. Следим за лайвом и готовим следующий блок рекомендаций."
            
            detailed_message = [
                f"🎯 LIVE-АНАЛИЗ • {time_str} МСК, {date_str}",
                "—————————————",
                "",
                no_matches_text,
                "",
                random.choice(discipline_tips),
                "—————————————",
            ]
            
            # Добавляем дисклеймер (расширенный список - 50 вариантов)
            from improve_telegram_messages import DISCLAIMERS_EXPANDED
            disclaimers = DISCLAIMERS_EXPANDED
            
            # Расширенные фразы для конца сообщения
            try:
                from improve_telegram_messages import CLOSING_PHRASES_EXPANDED
                closing_phrases = CLOSING_PHRASES_EXPANDED
                closing_phrase = random.choice(closing_phrases)
            except ImportError:
                closing_phrase = "🤖 @TrueLiveBet | Честные прогнозы с ИИ"
            
            detailed_message.extend([
                closing_phrase,
                "",
                random.choice(disclaimers),
            ])
            
            detailed_text = "\n".join(detailed_message)
            context["sections"] = [detailed_text]
            return (
                detailed_text,
                [],
                context,
            )
        else:
            # Простое сообщение с учетом количества подряд идущих "нет матчей"
            consecutive_count = increment_no_matches_count()
            
            # Получаем специальное сообщение в зависимости от количества
            if consecutive_count >= 3:
                # Используем специальные успокаивающие сообщения
                no_matches_text = get_no_matches_message_by_count(consecutive_count)
            else:
                # Обычное сообщение для первых 1-2 раз
                no_matches_text = "В данный момент подходящих матчей для рекомендации не найдено.\nСледующий анализ через 15 минут."
            
            simple_message = [
                f"🎯 LIVE-АНАЛИЗ • {time_str} МСК, {date_str}",
                "—————————————",
                "",
                no_matches_text,
                "",
                "—————————————",
                "🤖 @TrueLiveBet | Честные прогнозы с ИИ",
                "",
                "⚠️ Помните: даже лучшие прогнозы - это не гарантия. Играйте ответственно.",
            ]
            simple_text = "\n".join(simple_message)
            context["sections"] = [simple_text]
            return (
                simple_text,
                [],
                context,
            )

    # Разделяем матчи на безопасные и рискованные для гибридного подхода
    safe_matches = []
    risky_matches = []
    
    for match in selected_matches:
        odds_info = match.get("odds_info")
        odds_value = None
        if odds_info:
            if hasattr(odds_info, "value"):
                odds_value = odds_info.value
            elif isinstance(odds_info, dict):
                odds_value = odds_info.get("value")
        
        probability = match.get("claude_probability") or match.get("estimated_probability", 0)
        
        # Рискованные: коэффициенты 1.3-1.6 И вероятность 60-75%
        # ИЛИ коэффициент 1.4-1.6 (даже если вероятность выше 75%)
        # ИЛИ вероятность 60-70% (более рискованные)
        is_risky = False
        
        if odds_value:
            # Коэффициент в рискованном диапазоне 1.3-1.6
            if 1.3 <= odds_value <= 1.6:
                # Если вероятность низкая (60-75%) - точно рискованный
                if 60 <= probability <= 75:
                    is_risky = True
                # Если коэффициент высокий (1.4-1.6), но вероятность средняя - тоже рискованный
                elif 1.4 <= odds_value <= 1.6 and 70 <= probability <= 80:
                    is_risky = True
        
        # Вероятность в низком диапазоне 60-70% - всегда рискованный (даже если коэффициент низкий)
        if 60 <= probability <= 70:
            is_risky = True
        
        if is_risky:
            risky_matches.append(match)
        else:
            # Безопасные: все остальные (высокая вероятность 75-90%, низкие коэффициенты)
            safe_matches.append(match)
    
    # КРИТИЧЕСКОЕ: Разделяем матчи на новые и повторные (если повторные не отфильтрованы)
    filter_repeats = getattr(TUNING_SETTINGS, "filter_repeat_matches", True)
    
    if filter_repeats:
        # Повторные матчи уже отфильтрованы - работаем только с новыми
        new_safe_matches = safe_matches
        repeat_safe_matches = []
    else:
        # Разделяем на новые и повторные для показа в конце
        new_safe_matches = [m for m in safe_matches if not m.get("is_repeat", False)]
        repeat_safe_matches = [m for m in safe_matches if m.get("is_repeat", False)]
    
    # Группируем новые безопасные матчи по видам спорта
    safe_football = [m for m in new_safe_matches if m.get("sport_type") == "football"]
    safe_tennis = [m for m in new_safe_matches if m.get("sport_type") == "tennis"]
    safe_basketball = [m for m in new_safe_matches if m.get("sport_type") == "basketball"]
    safe_volleyball = [m for m in new_safe_matches if m.get("sport_type") == "volleyball"]
    safe_american_football = [m for m in new_safe_matches if m.get("sport_type") == "american_football"]
    safe_dota2 = [m for m in new_safe_matches if m.get("sport_type") == "dota2"]
    
    header = [
        f"🎯 LIVE-АНАЛИЗ • {time_str} МСК, {date_str}",
        "—————————————",
    ]

    message_parts: List[str] = ["\n".join(header)]

    # Сначала показываем новые матчи
    if safe_football:
        football_lines: List[str] = ["⚽ ФУТБОЛ ⚽"]
        for idx, match in enumerate(safe_football, 1):
            football_lines.append(_format_match_block(idx, match))
            # Добавляем пробел между матчами для лучшей читабельности
            if idx < len(safe_football):
                football_lines.append("")
        message_parts.append("\n".join(football_lines))

    if safe_tennis:
        tennis_lines: List[str] = ["🎾 ТЕННИС 🎾"]
        for idx, match in enumerate(safe_tennis, 1):
            tennis_lines.append(_format_tennis_block(idx, match))
            # Добавляем пробел между матчами для лучшей читабельности
            if idx < len(safe_tennis):
                tennis_lines.append("")
        message_parts.append("\n".join(tennis_lines))

    if safe_basketball:
        basketball_lines: List[str] = ["🏀 БАСКЕТБОЛ 🏀"]
        for idx, match in enumerate(safe_basketball, 1):
            basketball_lines.append(_format_basketball_block(idx, match))
        message_parts.append("\n".join(basketball_lines))

    if safe_volleyball:
        volleyball_lines: List[str] = ["🏐 ВОЛЕЙБОЛ 🏐"]
        for idx, match in enumerate(safe_volleyball, 1):
            volleyball_lines.append(_format_volleyball_block(idx, match))
        message_parts.append("\n".join(volleyball_lines))
    
    if safe_american_football:
        american_football_lines: List[str] = ["🏈 АМЕРИКАНСКИЙ ФУТБОЛ 🏈"]
        for idx, match in enumerate(safe_american_football, 1):
            american_football_lines.append(_format_american_football_block(idx, match))
        message_parts.append("\n".join(american_football_lines))
    
    if safe_dota2:
        dota2_lines: List[str] = ["🎮 DOTA 2 🎮"]
        for idx, match in enumerate(safe_dota2, 1):
            dota2_lines.append(_format_dota2_block(idx, match))
        message_parts.append("\n".join(dota2_lines))
    
    # КРИТИЧЕСКОЕ: Если повторные матчи не отфильтрованы, показываем их В КОНЦЕ
    if not filter_repeats and repeat_safe_matches:
        # Группируем повторные матчи по видам спорта
        repeat_football = [m for m in repeat_safe_matches if m.get("sport_type") == "football"]
        repeat_tennis = [m for m in repeat_safe_matches if m.get("sport_type") == "tennis"]
        repeat_basketball = [m for m in repeat_safe_matches if m.get("sport_type") == "basketball"]
        repeat_volleyball = [m for m in repeat_safe_matches if m.get("sport_type") == "volleyball"]
        repeat_american_football = [m for m in repeat_safe_matches if m.get("sport_type") == "american_football"]
        repeat_dota2 = [m for m in repeat_safe_matches if m.get("sport_type") == "dota2"]
        
        # Добавляем разделитель перед повторными матчами
        message_parts.append("")
        message_parts.append("⚠️ ПОВТОРНЫЕ МАТЧИ (коэффициенты могут быть уже низкими):")
        message_parts.append("")
        
        # Начинаем нумерацию с 1 для повторных матчей
        repeat_index = 1
        
        if repeat_football:
            repeat_football_lines: List[str] = ["⚽ ФУТБОЛ ⚽"]
            for match in repeat_football:
                repeat_football_lines.append(_format_match_block(repeat_index, match))
                repeat_index += 1
                repeat_football_lines.append("")
            message_parts.append("\n".join(repeat_football_lines))
        
        if repeat_tennis:
            repeat_tennis_lines: List[str] = ["🎾 ТЕННИС 🎾"]
            for match in repeat_tennis:
                repeat_tennis_lines.append(_format_tennis_block(repeat_index, match))
                repeat_index += 1
                repeat_tennis_lines.append("")
            message_parts.append("\n".join(repeat_tennis_lines))
        
        if repeat_basketball:
            repeat_basketball_lines: List[str] = ["🏀 БАСКЕТБОЛ 🏀"]
            for match in repeat_basketball:
                repeat_basketball_lines.append(_format_basketball_block(repeat_index, match))
                repeat_index += 1
            message_parts.append("\n".join(repeat_basketball_lines))
        
        if repeat_volleyball:
            repeat_volleyball_lines: List[str] = ["🏐 ВОЛЕЙБОЛ 🏐"]
            for match in repeat_volleyball:
                repeat_volleyball_lines.append(_format_volleyball_block(repeat_index, match))
                repeat_index += 1
            message_parts.append("\n".join(repeat_volleyball_lines))
        
        if repeat_american_football:
            repeat_american_football_lines: List[str] = ["🏈 АМЕРИКАНСКИЙ ФУТБОЛ 🏈"]
            for match in repeat_american_football:
                repeat_american_football_lines.append(_format_american_football_block(repeat_index, match))
                repeat_index += 1
            message_parts.append("\n".join(repeat_american_football_lines))
        
        if repeat_dota2:
            repeat_dota2_lines: List[str] = ["🎮 DOTA 2 🎮"]
            for match in repeat_dota2:
                repeat_dota2_lines.append(_format_dota2_block(repeat_index, match))
                repeat_index += 1
            message_parts.append("\n".join(repeat_dota2_lines))

    # Расширенный список дисклеймеров (50 вариантов)
    try:
        from improve_telegram_messages import DISCLAIMERS_EXPANDED
        disclaimer_options = DISCLAIMERS_EXPANDED
    except ImportError:
        # Fallback на старый список
        disclaimer_options = [
            "⚠️ Все ставки несут риски. Играй ответственно.",
            "⚠️ Ставки — не гарантированный доход. Контролируйте банк.",
            "⚠️ Нет безрисковых ставок. Обдумывайте решения самостоятельно.",
            "⚠️ Играйте ответственно. Ставки могут привести к зависимости.",
            "⚠️ Контролируйте свои эмоции. Холодный расчет важнее азарта.",
            "⚠️ Не ставьте больше, чем можете позволить себе потерять.",
            "⚠️ Помните: каждая ставка — это риск. Никаких гарантий.",
            "⚠️ Дисциплина превыше всего. Следуйте банкролл-менеджменту.",
            "⚠️ Ставки — это развлечение, а не способ заработка. Играйте с умом.",
            "⚠️ Если чувствуете, что теряете контроль — остановитесь.",
            "⚠️ Ответственная игра — основа долгосрочного успеха.",
            "⚠️ Не играйте на эмоциях. Принимайте решения трезво.",
        ]
    
    # Расширенный список фраз про дисциплину (для сообщений с матчами) - 60 вариантов
    try:
        from improve_telegram_messages import DISCIPLINE_TIPS_EXPANDED
        discipline_tips = DISCIPLINE_TIPS_EXPANDED
    except ImportError:
        # Fallback на старый список
        discipline_tips = [
            "📊 Поддерживай дисциплину банка: те же 2% на сигнал, без догонов.",
            "💡 Напоминание: не рискуйте более 2% банка на одну ставку.",
            "⏱️ Без суеты. Всё успеем — сначала смотрим цифры, потом ставим.",
            "🔍 Наши сигналы — только по проверенной статистике. Ставим не сердцем, а цифрами.",
            "📈 Спокойные ставки — залог долгосрочного успеха. Не торопимся.",
            "🎯 Дисциплина важнее азарта. Следуем системе, не эмоциям.",
            "💪 Терпение и выдержка — ключ к стабильной прибыли.",
            "📊 Отслеживай результаты: дата, матч, коэффициент и чем всё закончилось.",
            "🗂️ Любая ставка — зафиксируй купон или скрин: потом легче считать реальный профит.",
            "⚖️ Баланс — основа успеха. Не увеличивай ставки после проигрыша.",
            "🧠 Холодный расчет всегда побеждает эмоции. Доверяй системе.",
            "📉 После проигрыша — пауза. Не пытайся отыграться сразу.",
        ]
    
    # Случайный выбор дисклеймера и фразы про дисциплину
    disclaimer = random.choice(disclaimer_options)
    discipline_tip = random.choice(discipline_tips)

    # Статистика канала убрана - будет отправляться отдельно в конце дня
    footer = [
        "———————————————",
    ]
    
    footer.extend([
        discipline_tip,  # Добавляем фразу про дисциплину
        "",
        "🤖 @TrueLiveBet | Честные прогнозы с ИИ",
        "",
        disclaimer,
    ])

    # Формируем первое сообщение (безопасные матчи)
    message_sections = [part for part in message_parts if part]
    footer_text = "\n".join(footer)
    context["sections"] = message_sections + [footer_text]
    report_body = "\n\n".join(message_sections)
    report = "\n".join([report_body, footer_text])
    
    # Сохраняем разделение в контексте для формирования второго сообщения
    context["safe_matches"] = safe_matches
    context["risky_matches"] = risky_matches
    
    # Сбрасываем счетчик подряд идущих "нет матчей", так как матчи найдены
    from no_matches_tracker import reset_no_matches_count
    reset_no_matches_count()
    
    return report, selected_matches, context


if __name__ == "__main__":
    text, matches, _ = generate_live_report()
    print(text)

