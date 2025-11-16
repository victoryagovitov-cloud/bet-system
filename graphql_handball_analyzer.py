from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

from scores24_graphql_client import fetch_live_matches, fetch_match_stats

TOTAL_GAME_TIME = 60


ALLOWED_HANDBALL_KEYWORDS = [
    "liga чемпионов",
    "ehf champions league",
    "liga европы",
    "ehf european league",
    "seha",
    "bundesliga",
    "lnh",
    "asobal",
    "handboldligaen",
    "dameligaen",
    "vivé",
    "vivé kielce",
    "ekstraklasa",
    "premierliga",
    "lidl starligue",
    "hungary",
    "norway",
    "sweden",
    "denmark",
    "championship",
    "superliga",
    "olympic",
    "world championship",
    "euro",
]

DISALLOWED_HANDBALL_KEYWORDS = [
    "division 2",
    "second division",
    "youth",
    "reserve",
    "friendly",
    "exhibition",
    "challenge cup",
    "cup ehf",
    "вызова",
    "cup 2",
    "amateur",
]


def _is_allowed_handball_tournament(name: Optional[str]) -> bool:
    if not name:
        return True
    text = name.lower()
    if any(keyword in text for keyword in DISALLOWED_HANDBALL_KEYWORDS):
        return False
    if any(keyword in text for keyword in ALLOWED_HANDBALL_KEYWORDS):
        return True
    return True


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _parse_minute(value: Optional[Any]) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    match = re.search(r"(\d+)", text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def _parse_score(value: Optional[str]) -> Optional[Tuple[int, int]]:
    if not value:
        return None
    try:
        home, away = value.replace(" ", "").split(":")
        return int(home), int(away)
    except (ValueError, AttributeError):
        return None


def _project_total(total_score: int, minute_numeric: int) -> Optional[float]:
    if minute_numeric <= 0 or minute_numeric >= TOTAL_GAME_TIME:
        return None
    pace = total_score / minute_numeric
    remaining = TOTAL_GAME_TIME - minute_numeric
    return total_score + pace * remaining


def analyze_live_handball_matches(limit: int = 60) -> List[Dict[str, Any]]:
    live_matches = fetch_live_matches(limit=limit, sport="handball")
    analyzed: List[Dict[str, Any]] = []

    for match_info in live_matches:
        slug = match_info["slug"]
        try:
            details = fetch_match_stats(slug, sport="handball")
        except Exception:
            continue

        tournament_name = (
            (details.get("unique_tournament") or {}).get("name")
            or details.get("tournament_name")
            or match_info.get("tournament_name")
            or match_info.get("category_name")
            or match_info.get("league_slug")
            or ""
        )
        if not _is_allowed_handball_tournament(tournament_name):
            continue

        game_state = details.get("game_state") or {}
        home_score = _parse_int(game_state.get("home_score"))
        away_score = _parse_int(game_state.get("away_score"))
        if home_score is None or away_score is None:
            parsed = _parse_score(details.get("result_score"))
            if not parsed:
                continue
            home_score, away_score = parsed

        total_score = home_score + away_score
        
        minute_numeric = _parse_minute(details.get("minute") or match_info.get("minute"))
        
        # КРИТИЧЕСКИ ВАЖНО: НЕ используем оценку времени по счету!
        # Количество голов НЕ равно количеству минут в гандболе
        if minute_numeric is None:
            # Если минуты нет - пропускаем матч (нужна snapshot обогащение)
            continue
        
        # Проверяем валидность минуты
        if minute_numeric < 32:  # Слишком рано (меньше 32 минут)
            continue
        if minute_numeric >= TOTAL_GAME_TIME:  # Матч закончен
            continue
        if total_score < 20:  # Снижено с 25 до 20
            continue

        if home_score == away_score:
            continue

        leader_index = 0 if home_score > away_score else 1
        score_diff = abs(home_score - away_score)

        # Снижаем порог разницы: если >=40 мин - 3 гола, если >=45 мин - 2 гола
        if minute_numeric >= 45:
            diff_threshold = 2
        elif minute_numeric >= 40:
            diff_threshold = 3
        else:
            diff_threshold = 4
        if score_diff < diff_threshold:
            continue

        forecast_total = _project_total(total_score, minute_numeric)

        total_recommendation: Optional[Dict[str, Any]] = None
        if minute_numeric >= 36 and forecast_total is not None:
            rounded_total = int(round(forecast_total))
            if forecast_total >= 62:
                total_recommendation = {
                    "type": "over",
                    "label": "ТБ",
                    "value": rounded_total,
                }
            elif forecast_total <= 58:
                total_recommendation = {
                    "type": "under",
                    "label": "ТМ",
                    "value": rounded_total,
                }

        # Защита от деления на ноль
        if minute_numeric is None or minute_numeric <= 0:
            continue  # Пропускаем матч без валидного времени
        pace = total_score / minute_numeric
        dominance_score = score_diff * 5 + pace * 2
        if total_recommendation:
            dominance_score += 3

        teams = details.get("teams") or []
        if len(teams) < 2:
            continue
        home_name = teams[0].get("name", "").strip()
        away_name = teams[1].get("name", "").strip()
        if not home_name or not away_name:
            continue
        # Статистика опциональна - не отсеиваем если её нет
        # if details.get("statistic") and not details["statistic"].get("periods"):
        #     continue

        analyzed.append(
            {
                "sport": "handball",
                "slug": slug,
                "teams": [home_name, away_name],
                "score": f"{home_score}:{away_score}",
                "minute": str(minute_numeric),
                "minute_numeric": minute_numeric,
                "leader_index": leader_index,
                "score_diff": score_diff,
                "total_score": total_score,
                "pace": pace,
                "projected_total": forecast_total,
                "total_recommendation": total_recommendation,
                "dominance_score": dominance_score,
                "country": (details.get("country") or {}).get("name"),
                "tournament": (details.get("unique_tournament") or {}).get("name")
                or details.get("tournament_name"),
            }
        )

    analyzed.sort(key=lambda m: m.get("dominance_score", 0), reverse=True)
    return analyzed

