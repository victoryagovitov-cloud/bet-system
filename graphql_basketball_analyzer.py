from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

from scores24_graphql_client import fetch_live_matches, fetch_match_stats

LOWER_DIVISION_KEYWORDS = [
    "лига 2",
    "лига два",
    "вторая лига",
    "second division",
    "league two",
    "чемпионшип",
    "championship",
    "резерв",
    "women",
    "жен",
    "u21",
    "u20",
    "u19",
    "юнош",
    "до 21",
    "до 20",
    "до 19",
    "до 18",
    "до 17",
    "молодеж",
    "молодёж",
    "товарищ",
    "friendly",
    "дружеск",
    "test match",
    "тестовый",
    "подготовительный",
    "любительск",
    "amateur",
]

# Маркеры молодежных команд в названиях
YOUTH_TEAM_MARKERS = [
    "u21", "u20", "u19", "u18", "u17", "u16", "u15",
    "до 21", "до 20", "до 19", "до 18", "до 17", "до 16", "до 15",
    "u-21", "u-20", "u-19", "u-18", "u-17",
    "u/21", "u/20", "u/19", "u/18", "u/17",
    "молодеж", "молодёж", "юнош",
    "youth", "junior", "juniors",
]

TOP_CUP_KEYWORDS = [
    "nba",
    "euroleague",
    "евролига",
    "eurocup",
    "fib",
    "чемпионат мира",
    "world championship",
    "olympic",
    "олимпиада",
    "eurobasket",
    "европа",
    "europe",
    "acb",
    "liga acb",
    "vtb",
    "vtb united league",
    "superleague",
    "суперлига",
]


def _normalize(text: Optional[str]) -> str:
    if not text:
        return ""
    return " ".join(text.lower().split())


def _is_tournament_allowed(name: Optional[str]) -> bool:
    normalized = _normalize(name)
    if not normalized:
        return True

    # СНАЧАЛА проверяем запрещенные ключевые слова
    if any(keyword in normalized for keyword in LOWER_DIVISION_KEYWORDS):
        return False

    # ПОТОМ проверяем разрешенные (топовые турниры)
    if any(keyword in normalized for keyword in TOP_CUP_KEYWORDS):
        return True

    return True


def _is_youth_team(team_name: Optional[str]) -> bool:
    """Проверяет, является ли команда молодежной по названию"""
    if not team_name:
        return False
    normalized = _normalize(team_name)
    return any(marker in normalized for marker in YOUTH_TEAM_MARKERS)


MINIMUM_MINUTE_THRESHOLD = 3  # Минимум 3 минуты (уменьшено, так как минуты приходят как время в четверти, а не общая минута матча)


def _parse_numeric(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def _parse_score(details: Optional[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
    # Для баскетбола счет может быть в разных полях
    if not details:
        return None

    # 1. result_score (основной источник для баскетбола)
    result_score = details.get("result_score")
    if result_score:
        try:
            parts = str(result_score).replace(" ", "").split(":")
            if len(parts) == 2:
                return int(parts[0]), int(parts[1])
        except (ValueError, AttributeError):
            pass
    
    # 2. game_score
    game_score = details.get("game_score")
    if game_score:
        try:
            parts = str(game_score).replace(" ", "").split(":")
            if len(parts) == 2:
                return int(parts[0]), int(parts[1])
        except (ValueError, AttributeError):
            pass

    # 3. game_state
    game_state = details.get("game_state") or {}
    home_score = game_state.get("home_score")
    away_score = game_state.get("away_score")
    if home_score is not None and away_score is not None:
        try:
            return int(home_score), int(away_score)
        except (ValueError, TypeError):
            pass

    return None


def _extract_totals(statistic: Optional[Dict[str, Any]]) -> Dict[str, Tuple[Optional[float], Optional[float]]]:
    """Извлекает статистику из структуры Scores24 для баскетбола"""
    result: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
    if not statistic:
        return result

    periods = statistic.get("periods") or []
    if not periods:
        return result

    # Собираем статистику по периодам
    stats_by_name: Dict[str, List[float]] = {}
    for period in periods:
        groups = period.get("groups") or []
        for group in groups:
            statistics_items = group.get("statisticsItems") or []
            for item in statistics_items:
                name = item.get("name", "").lower()
                home_value = _parse_numeric(item.get("home"))
                away_value = _parse_numeric(item.get("away"))

                if name not in stats_by_name:
                    stats_by_name[name] = [[], []]
                if home_value is not None:
                    stats_by_name[name][0].append(home_value)
                if away_value is not None:
                    stats_by_name[name][1].append(away_value)

    # Суммируем по периодам
    for name, values in stats_by_name.items():
        home_total = sum(values[0]) if values[0] else None
        away_total = sum(values[1]) if values[1] else None
        result[name] = (home_total, away_total)

    return result


def _parse_minute_value(value: Optional[Any]) -> Optional[int]:
    """Парсит минуту матча для баскетбола.
    
    Форматы:
    - "Q1 3:17" -> 3 (минута в четверти) + 0 (четверть 1) = 3
    - "Q2 5:30" -> 5 + 10 = 15 (10 минут в Q1 + 5 в Q2)
    - "Q3 2:15" -> 2 + 20 = 22 (20 минут в Q1+Q2 + 2 в Q3)
    - "Q4 8:45" -> 8 + 30 = 38 (30 минут в Q1+Q2+Q3 + 8 в Q4)
    - "3:17" -> 3 (если формат времени в четверти)
    - "15" -> 15 (если уже общая минута)
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "—"}:
        return None
    
    # Пробуем найти формат "Q1 3:17" или "Q2 5:30"
    quarter_match = re.search(r"Q(\d+)\s*(\d+):\d+", text, re.IGNORECASE)
    if quarter_match:
        try:
            quarter = int(quarter_match.group(1))
            minute_in_quarter = int(quarter_match.group(2))
            # Q1: 0-10, Q2: 10-20, Q3: 20-30, Q4: 30-40
            total_minutes = (quarter - 1) * 10 + minute_in_quarter
            return total_minutes
        except (ValueError, IndexError):
            pass
    
    # Пробуем найти формат "3:17" (время в четверти) - берем только минуты
    time_match = re.match(r"(\d+):\d+", text)
    if time_match:
        try:
            # Это время в текущей четверти, но мы не знаем какая четверть
            # Берем как есть, но это может быть неточно
            minute_in_quarter = int(time_match.group(1))
            # Если меньше 10, скорее всего это минута в четверти
            # Но без информации о четверти сложно точно определить
            # Пока возвращаем как есть (будет неточно для Q2-Q4)
            return minute_in_quarter
        except (ValueError, IndexError):
            pass
    
    # Пробуем найти просто число (общая минута матча)
    number_match = re.match(r"(\d+)", text)
    if number_match:
        try:
            return int(number_match.group(1))
        except ValueError:
            return None
    
    return None


def analyze_live_basketball_matches(limit: int = 30) -> List[Dict[str, Any]]:
    live_matches = fetch_live_matches(limit, sport="basketball")
    analyzed: List[Dict[str, Any]] = []

    for match_info in live_matches:
        slug = match_info["slug"]
        try:
            details = fetch_match_stats(slug, sport="basketball")
        except Exception:
            continue

        score = _parse_score(details)
        if not score:
            score = _parse_score(match_info)
        if not score:
            continue
        home_score, away_score = score
        if home_score == away_score:
            continue

        totals = _extract_totals(details.get("statistic"))
        
        # Для баскетбола важны: очки (points), подборы (rebounds), передачи (assists)
        # Процент попаданий (field goal percentage) - опционально
        points = totals.get("points") or totals.get("очки")
        rebounds = totals.get("rebounds") or totals.get("подборы")
        assists = totals.get("assists") or totals.get("передачи")
        field_goal_pct = totals.get("field goal percentage") or totals.get("процент попаданий")
        
        # Если нет статистики points, используем счет из result_score как очки
        if not points or points[0] is None or points[1] is None:
            # Используем счет как очки (это основная метрика для баскетбола)
            points = (float(home_score), float(away_score))
        
        # Теперь points всегда есть (либо из статистики, либо из счета)

        teams = details.get("teams") or []
        if len(teams) < 2:
            continue

        raw_minute = (
            details.get("minute")
            or match_info.get("minute")
            or (details.get("game_state") or {}).get("minute")
            or (match_info.get("game_state") or {}).get("minute")
        )
        minute_str = str(raw_minute) if raw_minute is not None else ""
        minute_numeric = _parse_minute_value(details.get("minute"))
        if minute_numeric is None:
            minute_numeric = _parse_minute_value(match_info.get("minute"))
        if minute_numeric is None:
            minute_numeric = _parse_minute_value((details.get("game_state") or {}).get("minute"))
        if minute_numeric is None:
            minute_numeric = _parse_minute_value((match_info.get("game_state") or {}).get("minute"))
        if minute_numeric is not None and minute_numeric < MINIMUM_MINUTE_THRESHOLD:
            continue
        
        # Баскетбол: матч длится 40 минут (4 четверти по 10 минут)
        if minute_numeric is not None and minute_numeric >= 40:
            continue

        tournament = (
            (details.get("unique_tournament") or {}).get("name")
            or details.get("tournament_name")
            or match_info.get("tournament_name")
            or match_info.get("league_slug")
        )
        country_info = details.get("country") or match_info.get("country") or {}
        country_name = country_info.get("name")

        if not _is_tournament_allowed(tournament):
            continue

        home_name = teams[0].get("name")
        away_name = teams[1].get("name")
        
        # Проверяем названия команд на молодежные маркеры
        if _is_youth_team(home_name) or _is_youth_team(away_name):
            continue

        leader_index = 0 if home_score > away_score else 1
        trailing_index = 1 - leader_index

        status_code = (
            (details.get("status") or {}).get("code")
            or (match_info.get("status") or {}).get("code")
        )

        def _leader_value(metric: Tuple[Optional[float], Optional[float]]) -> float:
            value = metric[leader_index]
            return float(value) if value is not None else math.nan

        def _trailing_value(metric: Tuple[Optional[float], Optional[float]]) -> float:
            value = metric[trailing_index]
            return float(value) if value is not None else math.nan

        leader_metrics = {
            "points": _leader_value(points),
            "rebounds": _leader_value(rebounds) if rebounds else math.nan,
            "assists": _leader_value(assists) if assists else math.nan,
            "field_goal_pct": _leader_value(field_goal_pct) if field_goal_pct else math.nan,
        }

        trailing_metrics = {
            "points": _trailing_value(points),
            "rebounds": _trailing_value(rebounds) if rebounds else math.nan,
            "assists": _trailing_value(assists) if assists else math.nan,
            "field_goal_pct": _trailing_value(field_goal_pct) if field_goal_pct else math.nan,
        }

        # Расчет dominance_score для баскетбола
        # Учитываем: разницу в очках, подборы, передачи, процент попаданий, время матча
        score_diff = abs(home_score - away_score)
        
        # Учитываем время матча (баскетбол: 40 минут)
        time_factor = 1.0
        if minute_numeric is not None and minute_numeric > 0:
            time_factor = minute_numeric / 40.0  # 0.5 для 20-й минуты, 0.9 для 36-й
        
        # Учитываем текущий счет (разница очков)
        score_factor = score_diff * 1.5  # 10 очков = 15, 15 очков = 22.5
        
        # Компоненты dominance с проверками на math.nan
        points_component = 0.0
        if not math.isnan(leader_metrics["points"]) and not math.isnan(trailing_metrics["points"]):
            points_component = (leader_metrics["points"] - trailing_metrics["points"]) * 0.3
        
        rebounds_component = 0.0
        if not math.isnan(leader_metrics["rebounds"]) and not math.isnan(trailing_metrics["rebounds"]):
            rebounds_component = (leader_metrics["rebounds"] - trailing_metrics["rebounds"]) * 2
        
        assists_component = 0.0
        if not math.isnan(leader_metrics["assists"]) and not math.isnan(trailing_metrics["assists"]):
            assists_component = (leader_metrics["assists"] - trailing_metrics["assists"]) * 1.5
        
        fg_pct_component = 0.0
        if not math.isnan(leader_metrics["field_goal_pct"]) and not math.isnan(trailing_metrics["field_goal_pct"]):
            fg_pct_component = (leader_metrics["field_goal_pct"] - trailing_metrics["field_goal_pct"]) * 5
        
        # Улучшенная формула с учетом времени и счета
        dominance_score = (
            points_component
            + rebounds_component
            + assists_component
            + fg_pct_component
            + score_factor * time_factor  # Учитываем счет и время матча
        )
        
        # Проверяем, что dominance_score валидный (не nan)
        if math.isnan(dominance_score) or math.isinf(dominance_score):
            continue  # Пропускаем матч с невалидным dominance_score

        analyzed.append(
            {
                "sport": "basketball",
                "slug": slug,
                "teams": [home_name, away_name],
                "home_team": home_name,
                "away_team": away_name,
                "home_score": home_score,
                "away_score": away_score,
                "score": f"{home_score}:{away_score}",
                "minute": minute_str,
                "minute_numeric": minute_numeric,
                "leader_index": leader_index,
                "trailing_index": trailing_index,
                "leader_metrics": leader_metrics,
                "trailing_metrics": trailing_metrics,
                "dominance_score": dominance_score,
                "country": country_name,
                "tournament": tournament,
                "status_code": status_code,
            }
        )

    analyzed.sort(key=lambda m: m.get("dominance_score", 0), reverse=True)
    return analyzed

