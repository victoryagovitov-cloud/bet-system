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
from graphql_handball_analyzer import analyze_live_handball_matches
from graphql_basketball_analyzer import analyze_live_basketball_matches
from scores24_graphql_client import fetch_match_odds
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
        football_probability_floor: float = 0.60
        football_probability_cap: float = 0.90
        tennis_probability_floor: float = 0.70
        tennis_probability_cap: float = 0.92

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


MIN_ODDS = 1.01  # Минимальный коэффициент (оставляем все матчи)

_BASE_PRIMARY_MAX_ODDS = 1.10
_BASE_EXTENDED_MAX_ODDS = 1.50
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
    limit: int = 3,
    mcp_browser_navigate=None,
    mcp_browser_wait=None,
    mcp_browser_snapshot=None
) -> List[Dict]:
    matches = analyze_live_matches(limit=120)
    
    # Обогащаем данные через snapshot (если нужно)
    matches = _enrich_matches_with_snapshot(
        matches,
        "soccer",
        mcp_browser_navigate,
        mcp_browser_wait,
        mcp_browser_snapshot
    )
    
    filtered: List[Dict] = []
    for match in matches:
        # Анализируем все матчи с хоть каким-то перевесом (даже минимальным)
        dominance = match.get("dominance_score", 0)
        if dominance < -5.0:  # Только отфильтровываем явных аутсайдеров
            continue

        odds = _get_leader_odds(match["slug"], match["leader_index"])
        # Проверяем, что odds существует и value не None
        if odds is None or odds.value is None:
            continue
        
        # Фильтруем матчи с очень низкими коэффициентами
        if odds.value < MIN_ODDS:
            continue

        leader = match["leader_metrics"]
        trailing = match["trailing_metrics"]
        xg_diff = leader["xg"] - trailing["xg"]
        sot_diff = leader["shots_on_target"] - trailing["shots_on_target"]

        if odds.value <= PRIMARY_MAX_ODDS:
            # Безопасные матчи с идеальной статистикой (1.01-1.10)
            # Ужесточенные требования: нужен реальный перевес
            minute_numeric = match.get("minute_numeric") or 0
            
            # Для PRIMARY tier тоже учитываем время: ранние матчи требуют большего перевеса
            if minute_numeric < 30:
                # Ранний матч - нужен больший перевес даже для PRIMARY
                required_dominance = 5.0
            else:
                # Поздний матч - стандартные требования
                required_dominance = 2.0
            
            if dominance >= required_dominance or (xg_diff >= 0.2 and sot_diff >= 1):
                odds_tier = "primary"
            else:
                continue
        elif odds.value <= EXTENDED_MAX_ODDS:
            # Интересные матчи с более высокими коэффициентами (1.11-1.50)
            # Ужесточенные требования с учетом времени матча
            minute_numeric = match.get("minute_numeric") or 0
            
            # Учитываем время матча: для ранних матчей нужен больший перевес
            if minute_numeric < 30:
                # Ранний матч - нужен БОЛЬШОЙ перевес
                required_dominance = 8.0
            elif minute_numeric < 60:
                # Средний матч - стандартные требования
                required_dominance = EXTENDED_MIN_DOMINANCE
            else:
                # Поздний матч - можно немного снизить
                required_dominance = 5.0
            
            if (
                dominance >= required_dominance
                or (xg_diff >= EXTENDED_MIN_XG_DIFF and sot_diff >= EXTENDED_MIN_SOT_DIFF and minute_numeric >= 60)
            ):
                odds_tier = "extended"
            else:
                continue
        else:
            continue

        match["odds_info"] = odds
        match["odds_tier"] = odds_tier
        match["sport"] = "football"
        # Транслитерируем названия команд
        names = match.get("teams") or []
        if names:
            match["teams"] = [_transliterate_name(name) for name in names]
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
    limit: int = 2,
    mcp_browser_navigate=None,
    mcp_browser_wait=None,
    mcp_browser_snapshot=None
) -> List[Dict]:
    if limit <= 0:
        return []

    matches = analyze_live_tennis_matches(limit=80)
    
    # Обогащаем данные через snapshot (для завершенных сетов)
    matches = _enrich_matches_with_snapshot(
        matches,
        "tennis",
        mcp_browser_navigate,
        mcp_browser_wait,
        mcp_browser_snapshot
    )
    
    filtered: List[Dict] = []
    for match in matches:
        odds = _get_leader_odds(match["slug"], match["leader_index"], sport="tennis")
        # Проверяем, что odds существует и value не None
        if odds is None or odds.value is None:
            continue
        
        # Фильтруем матчи с очень низкими коэффициентами
        if odds.value < MIN_ODDS:
            continue

        points_diff = match.get("points_diff", 0)
        breaks_diff = match.get("breaks_diff", 0)

        dominance = match.get("dominance_score", 0)
        
        if odds.value <= PRIMARY_MAX_ODDS:
            # Безопасные матчи с идеальной статистикой (1.01-1.10)
            # Ужесточенные требования: нужен реальный перевес
            current_set = match.get("current_set", 1)
            total_games = match.get("total_games_played", 0)
            
            # Для тенниса учитываем сет: ранние матчи требуют большего перевеса
            if current_set == 1 and total_games < 6:
                # Очень ранний матч - нужен больший перевес
                required_dominance = 5.0
            else:
                # Поздний матч - стандартные требования
                required_dominance = 2.0
            
            if dominance >= required_dominance or (points_diff >= 3 and current_set >= 2):
                odds_tier = "primary"
            else:
                continue
        elif odds.value <= EXTENDED_MAX_ODDS:
            # Интересные матчи с более высокими коэффициентами (1.11-1.50)
            # Ужесточенные требования с учетом времени матча
            current_set = match.get("current_set", 1)
            total_games = match.get("total_games_played", 0)
            
            # Для тенниса учитываем сет и время через количество сыгранных геймов
            # Ранний матч (1-й сет, мало геймов) - нужен больший перевес
            if current_set == 1 and total_games < 6:
                # Очень ранний матч - нужен БОЛЬШОЙ перевес
                required_dominance = 8.0
            elif current_set == 1:
                # Первый сет - стандартные требования
                required_dominance = EXTENDED_MIN_DOMINANCE
            else:
                # Второй сет и дальше - можно немного снизить
                required_dominance = 5.0
            
            if (
                dominance >= required_dominance
                or (points_diff >= 4 and current_set >= 2)  # Для поздних сетов можно снизить требования
            ):
                odds_tier = "extended"
            else:
                continue
        else:
            continue

        match["odds_info"] = odds
        match["odds_tier"] = odds_tier
        match["sport"] = "tennis"
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
    limit: int = 3,
    mcp_browser_navigate=None,
    mcp_browser_wait=None,
    mcp_browser_snapshot=None
) -> List[Dict]:
    matches = analyze_live_basketball_matches(limit=120)
    
    # Обогащаем данные через snapshot (если нужно)
    matches = _enrich_matches_with_snapshot(
        matches,
        "basketball",
        mcp_browser_navigate,
        mcp_browser_wait,
        mcp_browser_snapshot
    )
    
    filtered: List[Dict] = []
    for match in matches:
        # Анализируем все матчи с хоть каким-то перевесом (даже минимальным)
        dominance = match.get("dominance_score", 0)
        if dominance < -5.0:  # Только отфильтровываем явных аутсайдеров
            continue

        odds = _get_leader_odds(match["slug"], match["leader_index"], sport="basketball")
        # Проверяем, что odds существует и value не None
        if odds is None or odds.value is None:
            continue
        
        # Фильтруем матчи с очень низкими коэффициентами
        if odds.value < MIN_ODDS:
            continue

        leader = match["leader_metrics"]
        trailing = match["trailing_metrics"]
        points_diff = leader["points"] - trailing["points"]
        rebounds_diff = leader["rebounds"] - trailing["rebounds"] if not math.isnan(leader["rebounds"]) else 0
        assists_diff = leader["assists"] - trailing["assists"] if not math.isnan(leader["assists"]) else 0

        if odds.value <= PRIMARY_MAX_ODDS:
            # Безопасные матчи с хорошей статистикой
            minute_numeric = match.get("minute_numeric") or 0
            
            # Для баскетбола учитываем время: ранние матчи требуют большего перевеса
            if minute_numeric < 20:  # Меньше половины матча
                required_dominance = 5.0 * RELAX_FACTOR
            else:
                required_dominance = 2.0 * RELAX_FACTOR
            
            if dominance >= required_dominance or (points_diff >= 8 and minute_numeric >= 25):
                odds_tier = "primary"
            else:
                continue
        elif odds.value <= EXTENDED_MAX_ODDS:
            # Интересные матчи с более высокими коэффициентами
            minute_numeric = match.get("minute_numeric") or 0
            
            # Учитываем время матча: для ранних матчей нужен больший перевес
            if minute_numeric < 20:
                required_dominance = 8.0 * RELAX_FACTOR
            elif minute_numeric < 30:
                required_dominance = EXTENDED_MIN_DOMINANCE
            else:
                required_dominance = 4.0 * RELAX_FACTOR
            
            if (
                dominance >= required_dominance
                or (points_diff >= 10 and rebounds_diff >= 2 and minute_numeric >= 25)
            ):
                odds_tier = "extended"
            else:
                continue
        else:
            continue

        match["odds_info"] = odds
        match["odds_tier"] = odds_tier
        match["sport"] = "basketball"
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


def _select_top_handball_matches(
    limit: int = 2,
    mcp_browser_navigate=None,
    mcp_browser_wait=None,
    mcp_browser_snapshot=None
) -> List[Dict]:
    if limit <= 0:
        return []

    matches = analyze_live_handball_matches(limit=80)
    
    # Обогащаем данные через snapshot (особенно важно для гандбола - там часто нет минут!)
    matches = _enrich_matches_with_snapshot(
        matches,
        "handball",
        mcp_browser_navigate,
        mcp_browser_wait,
        mcp_browser_snapshot
    )
    
    filtered: List[Dict] = []
    for match in matches:
        odds = _get_leader_odds(match["slug"], match["leader_index"], sport="handball")
        # Проверяем, что odds существует и value не None
        if odds is None or odds.value is None:
            continue
        
        # Фильтруем матчи с очень низкими коэффициентами
        if odds.value < MIN_ODDS:
            continue

        if odds.value <= PRIMARY_MAX_ODDS:
            odds_tier = "primary"
        elif (
            odds.value <= EXTENDED_MAX_ODDS
            and match.get("dominance_score", 0) >= EXTENDED_MIN_DOMINANCE
            and match.get("score_diff", 0) >= 3
        ):
            odds_tier = "extended"
        else:
            continue

        match["odds_info"] = odds
        match["odds_tier"] = odds_tier
        filtered.append(match)

    # Сортируем: сначала по коэффициенту (выше = лучше), потом по dominance
    filtered.sort(key=lambda m: (
        -(m.get("odds_info", OddsInfo(None, None)).value or 0),  # Сначала более высокие коэффициенты
        m.get("dominance_score", 0)  # Потом по dominance
    ), reverse=True)
    return filtered[:limit]


def _get_leader_odds(slug: str, leader_index: int, sport: str = "soccer") -> OddsInfo:
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

    probability = (
        60
        + xg_diff * 8
        + max(0, shots_ot_diff) * 4
        + max(0, shots_total_diff) * 1.2
        + max(0, possession_diff) * 0.12
        + score_gap * 3.5
    )
    probability = max(foot_floor, min(foot_cap, probability))
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

    probability = (
        58
        + set_advantage * 10
        + max(games_diff, 0) * 3
        + max(points_diff, 0) * 1.0
        + max(breaks_diff, 0) * 8
        + min(dominance, 25) * 0.5
    )
    probability = max(tennis_floor, min(tennis_cap, probability))
    return int(round(probability))


def _estimate_handball_probability(match: Dict) -> int:
    minute = match.get("minute_numeric") or 0
    score_diff = match.get("score_diff", 0)
    pace = match.get("pace", 0)
    projected = match.get("projected_total") or (match.get("total_score") or 0)
    remaining = max(0, 60 - minute)
    probability = (
        60
        + score_diff * 6
        + max(0, pace - 1) * 4
        + max(0, projected - 55) * 0.3
        - remaining * 0.25
    )
    probability = max(58, min(94, probability))
    return int(round(probability))


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

    analysis = (
        f"{leader_name} ведет {score} на {minute}' и подтверждает преимущество по {', '.join(parts)}."
    )

    if trailing["shots_on_target"] <= 1:
        analysis += f" {trailing_name} создал лишь {int(round(trailing['shots_on_target']))} опасный момент."
    else:
        analysis += f" {trailing_name} пока отвечает реже, но уступает по качеству моментов."

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
    # Исправляем логику: если счет по сетам 0:0, не пишем "ведёт по сетам 0:0"
    if sets_score == "0:0":
        analysis_parts.append(
            f"{leader_name} контролирует {_ordinal_set(current_set)} сет {games_home}:{games_away}."
        )
    else:
        analysis_parts.append(
            f"{leader_name} ведёт по сетам {sets_score} и контролирует {_ordinal_set(current_set)} сет "
            f"{games_home}:{games_away}."
        )
    points_diff = match.get("points_diff", 0)
    if points_diff >= 4:
        analysis_parts.append(
            f"По очкам {leader_name} впереди {_safe_int(points[leader_idx])} против {_safe_int(points[1 - leader_idx])}."
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

    block = [
        f"{index}. 🎾 {teams[0]} - {teams[1]}",
        f"🏟️ {location}",
        f"📊 Счёт: {sets_score} по сетам, {games_home}:{games_away} в {_ordinal_set(current_set)} сете",
        f"✅ Ставка: {bet_side} {leader_name}",
        "",
        "📈 РЕАЛЬНАЯ СТАТИСТИКА:",
        "\n".join(stats_lines),
        "",
        "🎯 АНАЛИЗ:",
        analysis,
        "",
        f"⚡ ВЕРОЯТНОСТЬ: ~{probability}%",
    ]
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

    analysis_parts: List[str] = []
    analysis_parts.append(
        f"{leader_name} ведёт {score_diff} мяч(а) на {minute}-й минуте и контролирует игру."
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

    block = [
        f"{index}. 🤾 {teams[0]} - {teams[1]}",
        f"🏟️ {location}",
        f"📊 Счёт: {score} ({minute}' мин)",
        f"✅ Ставка: {bet_side} {leader_name}",
        "",
        "📈 РЕАЛЬНАЯ СТАТИСТИКА:",
        "\n".join(stats_lines),
        "",
        "🎯 АНАЛИЗ:",
        analysis,
        "",
        f"⚡ ВЕРОЯТНОСТЬ: ~{probability}%",
    ]
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
    tournament = match.get("tournament")
    country = match.get("country")
    location_parts = [part for part in (country, tournament) if part]
    location = " • ".join(location_parts) if location_parts else "—"

    probability = _estimate_probability(match)
    match["estimated_probability"] = probability

    has_xg = match.get("has_xg", False)
    possession_home, possession_away = match["possession"]
    shots_total_data = match.get("shots_total")
    has_shots_total = shots_total_data is not None and len(shots_total_data) == 2 and shots_total_data[0] is not None and shots_total_data[1] is not None
    sot_home, sot_away = match["shots_on_target"]

    bet_side = "П1" if leader_idx == 0 else "П2"

    stats_lines = []
    if has_xg:
        xg_home, xg_away = match["xg"]
        stats_lines.append(f"* xG: {xg_home:.2f} - {xg_away:.2f}")
    else:
        stats_lines.append("* xG: отсутствует")
    stats_lines.append(f"* Владение: {int(round(possession_home))}% - {int(round(possession_away))}%")
    if has_shots_total:
        shots_home, shots_away = shots_total_data
        stats_lines.append(f"* Удары: {int(round(shots_home))} - {int(round(shots_away))}")
    else:
        stats_lines.append("* Удары: отсутствуют")
    stats_lines.extend([
        f"* Удары в створ: {int(round(sot_home))} - {int(round(sot_away))}",
        f"* Позиции: {_format_positions(match)}",
    ])
    stats_block = "\n".join(stats_lines)

    analysis = _format_analysis(match)

    if match.get("odds_tier") == "extended":
        analysis += " Коэффициент выше базового диапазона — контролируем размер ставки."
    
    # Добавляем пометку об отсутствии xG
    if not has_xg:
        analysis += " ⚠️ По данному матчу отсутствует показатель xG — будьте осторожнее."

    block = [
        f"{index}. 🎯 {teams[0]} - {teams[1]}",
        f"🏟️ {location}",
        f"📊 Счет: {score} ({minute}', live)",
        f"✅ Ставка: {bet_side} {leader_name}",
        "",
        "📈 РЕАЛЬНАЯ СТАТИСТИКА:",
        stats_block,
        "",
        "🎯 АНАЛИЗ:",
        analysis,
        "",
        f"⚡ ВЕРОЯТНОСТЬ: ~{probability}%",
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

    analysis = (
        f"{leader_name} ведет {score} на {minute}' и контролирует игру {', '.join(analysis_parts)}. "
        f"{trailing_name} пока уступает по качеству моментов."
    )

    if match.get("odds_tier") == "extended":
        analysis += " Коэффициент выше базового диапазона — контролируем размер ставки."

    probability = _estimate_basketball_probability(match)
    match["estimated_probability"] = probability

    block_lines = [
        f"{index}. 🏀 {teams[0]} - {teams[1]}",
        f"🏟️ {location}",
        f"📊 Счет: {score} ({minute}', live)",
        f"✅ Ставка: {'П1' if leader_idx == 0 else 'П2'} {leader_name}",
        "",
        "📈 РЕАЛЬНАЯ СТАТИСТИКА:",
        stats_block,
        "",
        f"🎯 АНАЛИЗ:\n{analysis}",
        "",
        f"⚡ ВЕРОЯТНОСТЬ: ~{probability}%",
    ]
    return "\n".join(block_lines)


def _get_recent_slugs(hours: int = 4) -> set[str]:
    """Получает список slug матчей, отправленных за последние N часов."""
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


def _filter_duplicates(matches: List[Dict], recent_slugs: set[str]) -> List[Dict]:
    """Фильтрует матчи, которые уже были отправлены недавно."""
    filtered = []
    filtered_count = 0
    for match in matches:
        slug = match.get("slug", "").strip()
        if slug and slug in recent_slugs:
            filtered_count += 1
            if filtered_count <= 3:  # Показываем первые 3 отфильтрованных
                print(f"DEBUG: Filtered duplicate match: {slug}")
            continue
        filtered.append(match)
    if filtered_count > 3:
        print(f"DEBUG: ... and {filtered_count - 3} more matches filtered as duplicates")
    return filtered


def generate_live_report(
    max_matches: int = 3,
    mcp_browser_navigate=None,
    mcp_browser_wait=None,
    mcp_browser_snapshot=None
) -> Tuple[str, List[Dict], Dict[str, Any]]:
    now = datetime.now(ZoneInfo("Europe/Moscow"))
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%d.%m.%Y")
    context: Dict[str, Any] = {
        "generated_at": now,
        "time_str": time_str,
        "date_str": date_str,
    }
    
    # Получаем список недавно отправленных матчей (за последние 4 часа)
    recent_slugs = _get_recent_slugs(hours=4)

    # Увеличиваем лимит поиска для большего разнообразия
    football_matches = _select_top_matches(
        limit=max_matches * 2,  # Ищем больше, чтобы было из чего выбирать
        mcp_browser_navigate=mcp_browser_navigate,
        mcp_browser_wait=mcp_browser_wait,
        mcp_browser_snapshot=mcp_browser_snapshot
    )
    remaining_slots = max(0, max_matches - len(football_matches))

    tennis_limit = 0
    if len(football_matches) == 0:
        tennis_limit = max(1, remaining_slots or 1)
    elif remaining_slots > 0:
        tennis_limit = remaining_slots
    # Увеличиваем лимит поиска для тенниса
    tennis_matches = _select_top_tennis_matches(
        limit=tennis_limit * 2 if tennis_limit > 0 else 0,  # Ищем больше для разнообразия
        mcp_browser_navigate=mcp_browser_navigate,
        mcp_browser_wait=mcp_browser_wait,
        mcp_browser_snapshot=mcp_browser_snapshot
    )

    # Обновляем оставшиеся слоты после футбола и тенниса
    remaining_slots_after_tennis = max(0, max_matches - len(football_matches) - len(tennis_matches))
    
    # Баскетбол
    basketball_limit = 0
    if remaining_slots_after_tennis > 0:
        basketball_limit = remaining_slots_after_tennis
    basketball_matches = _select_top_basketball_matches(
        limit=basketball_limit * 2 if basketball_limit > 0 else 0,
        mcp_browser_navigate=mcp_browser_navigate,
        mcp_browser_wait=mcp_browser_wait,
        mcp_browser_snapshot=mcp_browser_snapshot
    )
    
    # Гандбол отключен (проблема с получением минут из API)
    # remaining_slots_after_basketball = max(0, max_matches - len(football_matches) - len(tennis_matches) - len(basketball_matches))
    # handball_limit = 0
    # if remaining_slots_after_basketball > 0:
    #     handball_limit = remaining_slots_after_basketball
    # handball_matches = _select_top_handball_matches(
    #     limit=handball_limit * 2 if handball_limit > 0 else 0,
    #     mcp_browser_navigate=mcp_browser_navigate,
    #     mcp_browser_wait=mcp_browser_wait,
    #     mcp_browser_snapshot=mcp_browser_snapshot
    # )
    handball_matches = []  # Гандбол отключен

    selected_matches = football_matches + tennis_matches + basketball_matches + handball_matches
    
    # Логируем количество матчей до дедупликации
    matches_before_dedup = len(selected_matches)
    if matches_before_dedup > 0:
        print(f"DEBUG: Found {matches_before_dedup} matches before deduplication")
        print(f"DEBUG: Recent slugs in deduplication window: {len(recent_slugs)}")
    
    # Фильтруем дубликаты (матчи, которые уже были отправлены)
    selected_matches_before = selected_matches.copy()
    selected_matches = _filter_duplicates(selected_matches, recent_slugs)
    
    # Логируем количество матчей после дедупликации
    matches_after_dedup = len(selected_matches)
    if matches_before_dedup > 0:
        print(f"DEBUG: After deduplication: {matches_after_dedup} matches (filtered {matches_before_dedup - matches_after_dedup})")
        # Показываем slugs оставшихся матчей для отладки
        if matches_after_dedup > 0:
            remaining_slugs = [m.get("slug", "?") for m in selected_matches]
            print(f"DEBUG: Remaining slugs: {remaining_slugs}")
    if matches_before_dedup > 0 and matches_after_dedup == 0:
        print(f"WARNING: All {matches_before_dedup} matches were filtered by deduplication!")
        print(f"DEBUG: Matches were filtered because they were sent in the last 4 hours")
    
    # Ограничиваем финальное количество матчей в сообщении
    # Но теперь у нас больше разнообразия для выбора
    if len(selected_matches) > max_matches:
        # Приоритизируем матчи с более высокими коэффициентами
        selected_matches.sort(key=lambda m: (
            -(m.get("odds_info", OddsInfo(None, None)).value or 0),
            m.get("dominance_score", 0)
        ), reverse=True)
        selected_matches = selected_matches[:max_matches]

    if not selected_matches:
        # Чередуем два типа сообщений когда нет матчей
        # Используем время для детерминированного чередования
        use_detailed = (now.hour * 60 + now.minute) % 40 < 20  # Чередуем каждые 20 минут
        
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
            
            detailed_message = [
                f"🎯 LIVE-АНАЛИЗ • {time_str} МСК, {date_str}",
                "—————————————",
                "",
                "Сейчас подходящих матчей в топ-лигах нет. Следим за лайвом и готовим следующий блок рекомендаций.",
                "",
                random.choice(discipline_tips),
                "—————————————",
            ]
            
            # Добавляем дисклеймер (12 вариантов)
            disclaimers = [
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
            
            detailed_message.extend([
                "🤖 @TrueLiveBet | Честные прогнозы с ИИ",
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
            # Простое сообщение
            simple_message = "В данный момент подходящих матчей для рекомендации не найдено. Следующий анализ через 20 минут."
            context["sections"] = [simple_message]
            return (
                simple_message,
                [],
                context,
            )

    header = [
        f"🎯 LIVE-АНАЛИЗ • {time_str} МСК, {date_str}",
        "—————————————",
    ]

    message_parts: List[str] = ["\n".join(header)]

    if football_matches:
        football_lines: List[str] = ["⚽ ФУТБОЛ ⚽", "—————————————"]
        for idx, match in enumerate(football_matches, 1):
            football_lines.append(_format_match_block(idx, match))
            if idx < len(football_matches):
                football_lines.append("—————————————")
        message_parts.append("\n".join(football_lines))

    if tennis_matches:
        tennis_lines: List[str] = ["🎾 ТЕННИС 🎾", "—————————————"]
        for idx, match in enumerate(tennis_matches, 1):
            tennis_lines.append(_format_tennis_block(idx, match))
            if idx < len(tennis_matches):
                tennis_lines.append("—————————————")
        message_parts.append("\n".join(tennis_lines))

    if basketball_matches:
        basketball_lines: List[str] = ["🏀 БАСКЕТБОЛ 🏀", "—————————————"]
        for idx, match in enumerate(basketball_matches, 1):
            basketball_lines.append(_format_basketball_block(idx, match))
            if idx < len(basketball_matches):
                basketball_lines.append("—————————————")
        message_parts.append("\n".join(basketball_lines))

    if handball_matches:
        handball_lines: List[str] = ["🤾 ГАНДБОЛ 🤾", "—————————————"]
        for idx, match in enumerate(handball_matches, 1):
            handball_lines.append(_format_handball_block(idx, match))
            if idx < len(handball_matches):
                handball_lines.append("—————————————")
        message_parts.append("\n".join(handball_lines))

    # Расширенный список дисклеймеров (12 вариантов)
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
    
    # Расширенный список фраз про дисциплину (для сообщений с матчами)
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

    footer = [
        "———————————————",
        discipline_tip,  # Добавляем фразу про дисциплину
        "",
        "🤖 @TrueLiveBet | Честные прогнозы с ИИ",
        "",
        disclaimer,
    ]

    message_sections = [part for part in message_parts if part]
    footer_text = "\n".join(footer)
    context["sections"] = message_sections + [footer_text]
    report_body = "\n\n".join(message_sections)
    report = "\n".join([report_body, footer_text])
    return report, selected_matches, context


if __name__ == "__main__":
    text, matches, _ = generate_live_report()
    print(text)

