from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

from scores24_graphql_client import fetch_live_matches, fetch_match_stats


def _parse_pair(value: Optional[str]) -> Optional[Tuple[int, int]]:
    if not value:
        return None
    try:
        left, right = value.replace(" ", "").split(":")
        return int(left), int(right)
    except (ValueError, AttributeError):
        return None


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


# Известные турниры Dota 2 с хорошей статистикой
TOP_DOTA2_TOURNAMENTS = [
    "the international",
    "ti",
    "major",
    "dpc",
    "dreamleague",
    "esl",
    "epicenter",
    "pgl",
    "weplay",
    "bts",
    "beyond the summit",
    "esl one",
    "star ladder",
    "weplay animajor",
    "animajor",
    "riyadh masters",
    "betboom",
    "betboom dacha",
    "dacha",
    "gamers galaxy",
    "pinnacle",
    "pinnacle cup",
    "omega league",
    "omega",
    "omen",
    "omen by esl",
    "china dota2",
    "cdec",
    "perfect world",
    "perfect world masters",
    "cda",
    "china dota2 professional",
    "dota pro circuit",
    "dpc",
    "regional league",
    "division i",
    "division 1",
    "division ii",
    "division 2",
]


# Малоизвестные турниры (только счет, статистика с задержкой)
LOW_TIER_DOTA2_TOURNAMENTS = [
    "qualifier",
    "open qualifier",
    "closed qualifier",
    "amateur",
    "youth",
    "junior",
    "u18",
    "u20",
    "community",
    "local",
    "regional",
    "division 3",
    "division iii",
    "division 4",
    "division iv",
]


def _is_top_tier_dota2_tournament(name: Optional[str]) -> bool:
    """Проверяет, является ли турнир топовым (с хорошей статистикой)"""
    if not name:
        return False
    text = name.lower()
    # Если есть маркеры низкоуровневых турниров - не топ
    if any(keyword in text for keyword in LOW_TIER_DOTA2_TOURNAMENTS):
        return False
    # Если есть маркеры топовых турниров - топ
    if any(keyword in text for keyword in TOP_DOTA2_TOURNAMENTS):
        return True
    # По умолчанию считаем топовым, если нет явных маркеров низкого уровня
    return True


def _extract_stats(statistic: Optional[Dict[str, Any]]) -> Dict[str, Tuple[float, float]]:
    """Извлекает статистику из GraphQL ответа"""
    metrics: Dict[str, Tuple[float, float]] = {}
    if not statistic:
        return metrics
    for period in statistic.get("periods") or []:
        if period.get("type") != "total":
            continue
        for group in period.get("groups") or []:
            for item in group.get("items") or []:
                key = item.get("type")
                if not key:
                    continue
                team1 = item.get("team1_value")
                team2 = item.get("team2_value")
                try:
                    metrics[key] = (float(team1), float(team2))
                except (TypeError, ValueError):
                    metrics[key] = (math.nan, math.nan)
    return metrics


def _parse_game_time(value: Optional[Any]) -> Optional[int]:
    """Парсит время игры в минутах из строки (например, "35:23" -> 35)"""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    # Ищем паттерн "MM:SS" или просто число минут
    match = re.search(r"(\d+):\d+", text)
    if match:
        return int(match.group(1))
    # Если просто число
    match = re.search(r"^(\d+)$", text)
    if match:
        return int(match.group(1))
    return None


def analyze_live_dota2_matches(limit: int = 60) -> List[Dict[str, Any]]:
    """
    Анализирует live матчи по Dota 2
    
    КРИТИЧЕСКИ ВАЖНО:
    - Ставки делаются на победу в КОНКРЕТНОЙ КАРТЕ (раунде), а не во всем матче
    - На новой карте будут новые герои - предугадать исход очень трудно
    - Поэтому анализируем только текущую карту
    
    Критерии отбора:
    1. Только топовые турниры (с хорошей статистикой)
    2. Минимум 30 минут игры (тайм-аут как в футболе)
    3. Лидер должен вести минимум 1:0 по картам (для BO3) или 2:0/2:1 (для BO5)
    4. В текущей карте лидер должен вести минимум с разницей в 5 убийств
    5. Разница в Net Worth должна быть минимум +2000 золота
    6. Лидер должен иметь больше золота (если ведет по убийствам, но отстает по золоту - плохо)
    """
    # Пробуем разные slug для Dota 2
    sport_slugs = ["dota2", "dota"]
    live_matches = []
    
    for slug in sport_slugs:
        try:
            matches = fetch_live_matches(limit=limit, sport=slug)
            if matches:
                live_matches = matches
                break
        except Exception:
            continue
    
    if not live_matches:
        return []
    
    analyzed: List[Dict[str, Any]] = []

    for match_info in live_matches:
        slug = match_info["slug"]
        try:
            # Пробуем разные slug для получения статистики
            details = None
            for sport_slug in sport_slugs:
                try:
                    details = fetch_match_stats(slug, sport=sport_slug)
                    if details:
                        break
                except Exception:
                    continue
            
            if not details:
                continue
        except Exception:
            continue

        tournament_name = (
            (details.get("unique_tournament") or {}).get("name")
            or details.get("tournament_name")
            or match_info.get("tournament_name")
            or match_info.get("category_name")
            or ""
        )
        
        # КРИТИЧЕСКОЕ: Только топовые турниры с хорошей статистикой
        if not _is_top_tier_dota2_tournament(tournament_name):
            continue

        # Получаем счет по картам
        result_score = _parse_pair(details.get("result_score"))
        maps_home = result_score[0] if result_score else 0
        maps_away = result_score[1] if result_score else 0

        # Получаем счет в текущей карте (убийства)
        result_scores = details.get("result_scores") or []
        current_map_score = (0, 0)
        current_map_index = 1
        
        if result_scores:
            last_entry = result_scores[-1]
            current_map_score = _parse_pair(last_entry.get("value")) or (0, 0)
            type_raw = str(last_entry.get("type") or "")
            if type_raw.isdigit():
                current_map_index = int(type_raw)
            else:
                current_map_index = len(result_scores)

        # Проверяем статус матча
        status_code = (details.get("status") or {}).get("code")
        if status_code in {"100", "110"}:  # finished or suspended
            continue

        # Определяем лидера
        leader_index: Optional[int] = None
        map_diff = maps_home - maps_away
        kills_home, kills_away = current_map_score

        if map_diff > 0:
            leader_index = 0
        elif map_diff < 0:
            leader_index = 1
        else:
            # Если карт равное количество, проверяем текущую карту
            if abs(kills_home - kills_away) < 5:
                continue  # Слишком маленькая разница
            leader_index = 0 if kills_home > kills_away else 1

        if leader_index is None:
            continue

        trailing_index = 1 - leader_index

        # КРИТИЧЕСКОЕ: Только матчи с преимуществом минимум 1 карта (1:0 для BO3, 2:0/2:1 для BO5)
        # НЕ анализируем матчи с ничьей по картам (0:0, 1:1) - слишком рискованно
        if abs(map_diff) == 0:
            continue  # НЕ анализируем матчи с ничьей по картам

        # КРИТИЧЕСКОЕ: В текущей карте лидер должен вести минимум с разницей в 5 убийств
        kills_diff = abs(kills_home - kills_away)
        if kills_diff < 5:
            continue

        # Извлекаем статистику
        stats_map = _extract_stats(details.get("statistic"))
        
        # Ключевые метрики для Dota 2:
        # - kills (убийства) - 1000 монет за каждое
        # - net_worth или gold (золото/чистая стоимость) - КРИТИЧНО
        # - towers (башни) - нужно уточнить награду
        # - gold (золото) - деньги = предметы = усиление героев
        
        kills = stats_map.get("kills") or stats_map.get("kills_total")
        net_worth = stats_map.get("net_worth") or stats_map.get("gold") or stats_map.get("total_gold")
        towers = stats_map.get("towers") or stats_map.get("towers_destroyed")
        gold = stats_map.get("gold") or stats_map.get("total_gold") or net_worth

        # КРИТИЧЕСКОЕ: Проверяем золото (Net Worth)
        # Если команда ведет по убийствам и башням, но отстает по золоту - это плохо
        # Это говорит о более слабой игре в лесу и фарме
        if net_worth:
            net_worth_leader = net_worth[leader_index]
            net_worth_trailing = net_worth[trailing_index]
            
            # Если лидер отстает по золоту - это плохой знак
            if net_worth_leader < net_worth_trailing:
                continue  # НЕ анализируем такие матчи
            
            # Разница в Net Worth должна быть минимум +2000 золота
            net_worth_diff = net_worth_leader - net_worth_trailing
            if net_worth_diff < 2000:
                continue

        # КРИТИЧЕСКОЕ: Тайм-аут - не анализируем слишком ранние матчи
        # Предлагаю 30 минут (как в футболе), но можно и 25-35 минут
        # В Dota 2 игра обычно длится 30-50 минут, поэтому 30 минут - хороший момент
        game_time = _parse_game_time(details.get("minute") or match_info.get("minute"))
        MINIMUM_GAME_TIME = 30  # Минимум 30 минут игры
        
        if game_time is None or game_time < MINIMUM_GAME_TIME:
            continue  # Слишком ранний матч

        # Вычисляем dominance_score
        map_advantage = abs(map_diff) * 15  # Преимущество по картам (важно!)
        kills_advantage = kills_diff * 2  # Преимущество в убийствах
        
        dominance_score = map_advantage + kills_advantage

        # Добавляем статистику, если есть
        if net_worth:
            net_worth_diff = net_worth[leader_index] - net_worth[trailing_index]
            dominance_score += max(net_worth_diff / 1000, 0)  # 1000 золота = 1 балл

        if towers:
            towers_diff = towers[leader_index] - towers[trailing_index]
            dominance_score += towers_diff * 3  # Башня = 3 балла

        # Проверяем валидность
        if math.isnan(dominance_score) or math.isinf(dominance_score) or dominance_score <= 0:
            continue

        teams = details.get("teams") or []
        if len(teams) < 2:
            continue
        home_name = teams[0].get("name", "").strip()
        away_name = teams[1].get("name", "").strip()
        if not home_name or not away_name:
            continue

        analyzed.append(
            {
                "sport": "dota2",
                "slug": slug,
                "teams": [home_name, away_name],
                "status_code": status_code,
                "maps_score": f"{maps_home}:{maps_away}",
                "current_map": current_map_index,
                "current_map_score": current_map_score,
                "game_time": game_time,
                "leader_index": leader_index,
                "dominance_score": dominance_score,
                "kills": kills,
                "net_worth": net_worth,
                "gold": gold,
                "towers": towers,
                "tournament": (details.get("unique_tournament") or {}).get("name")
                or details.get("tournament_name"),
                "country": (details.get("country") or {}).get("name"),
                "is_top_tier": _is_top_tier_dota2_tournament(tournament_name),
            }
        )

    analyzed.sort(key=lambda m: m.get("dominance_score", 0), reverse=True)
    return analyzed

