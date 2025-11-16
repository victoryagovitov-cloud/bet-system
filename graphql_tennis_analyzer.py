from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from scores24_graphql_client import fetch_live_matches, fetch_match_odds, fetch_match_stats


def _parse_pair(value: Optional[str]) -> Optional[Tuple[int, int]]:
    if not value:
        return None
    try:
        left, right = value.replace(" ", "").split(":")
        return int(left), int(right)
    except (ValueError, AttributeError):
        return None


def _is_set_finished(score: Tuple[int, int]) -> bool:
    home, away = score
    if max(home, away) < 6:
        return False
    if max(home, away) == 6:
        return abs(home - away) >= 2
    return True  # 7 or more implies tie-break resolved


def _extract_stats(statistic: Optional[Dict[str, Any]]) -> Dict[str, Tuple[float, float]]:
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


def _current_set_info(result_scores: List[Dict[str, Any]]) -> Tuple[int, Tuple[int, int]]:
    if not result_scores:
        return 1, (0, 0)
    last_entry = result_scores[-1]
    games = _parse_pair(last_entry.get("value")) or (0, 0)
    type_raw = str(last_entry.get("type") or "")
    if type_raw.isdigit():
        set_index = int(type_raw)
    else:
        set_index = len(result_scores)
    if _is_set_finished(games) and len(result_scores) > 1:
        # last finished set; take previous as completed, current is new (0:0)
        return set_index + 1, (0, 0)
    return set_index, games


ALLOWED_TENNIS_KEYWORDS = [
    "atp",
    "wta",
    "challenger",
    "челленджер",  # Русское название
    "itf",  # ITF турниры - разрешены, если есть статистика
    "tour finals",
    "итоговый турнир",  # Русское название ATP Finals
    "cup",
    "кубок",  # Русское название
    "masters",
    "мастерс",  # Русское название
    "grand slam",
    "большой шлем",  # Русское название
    "billie jean king",
    "davis cup",
    "кубок дейвиса",  # Русское название
    "hopman cup",
    "united cup",
]


DISALLOWED_TENNIS_KEYWORDS = [
    # "itf" - убрано, теперь разрешено если есть статистика
    "futures",
    "future",
    "exhibition",
    "junior",
    "u18",
    "u20",
    "u21",
    "club league",
]


def _is_allowed_tennis_tournament(name: Optional[str]) -> bool:
    if not name:
        return False
    text = name.lower()
    if any(keyword in text for keyword in DISALLOWED_TENNIS_KEYWORDS):
        return False
    if any(keyword in text for keyword in ALLOWED_TENNIS_KEYWORDS):
        return True
    return False


def analyze_live_tennis_matches(limit: int = 60) -> List[Dict[str, Any]]:
    live_matches = fetch_live_matches(limit=limit, sport="tennis")
    analyzed: List[Dict[str, Any]] = []

    for match_info in live_matches:
        slug = match_info["slug"]
        try:
            details = fetch_match_stats(slug, sport="tennis")
        except Exception:
            continue

        tournament_name = (
            (details.get("unique_tournament") or {}).get("name")
            or details.get("tournament_name")
            or match_info.get("tournament_name")
            or match_info.get("category_name")
        )
        # Если название турнира отсутствует или "N/A", пропускаем проверку фильтра
        # (матч будет проверен по другим критериям - сеты, геймы, статистика)
        if tournament_name and tournament_name.strip().upper() not in ("N/A", ""):
            if not _is_allowed_tennis_tournament(tournament_name):
                continue

        result_score = _parse_pair(details.get("result_score"))
        sets_home = result_score[0] if result_score else 0
        sets_away = result_score[1] if result_score else 0

        result_scores = details.get("result_scores") or []
        current_set_index, current_games = _current_set_info(result_scores)
        games_home, games_away = current_games

        total_games_played = sum(
            sum(_parse_pair(entry.get("value")) or (0, 0)) for entry in result_scores
        )
        status_code = (details.get("status") or {}).get("code")
        if status_code in {"100", "110"}:  # finished or suspended
            continue

        leader_index: Optional[int] = None
        set_diff = sets_home - sets_away
        game_diff = games_home - games_away

        if set_diff > 0:
            leader_index = 0
        elif set_diff < 0:
            leader_index = 1
        else:
            if abs(game_diff) < 2:
                continue
            leader_index = 0 if game_diff > 0 else 1

        trailing_index = 1 - leader_index

        stats_map = _extract_stats(details.get("statistic"))
        points = stats_map.get("points_won")
        service_points_won = stats_map.get("service_points_won")
        breakpoints_won = stats_map.get("breakpoints_won")
        total_breakpoints = stats_map.get("total_breakpoints")

        # Для ITF матчей требуем наличие хотя бы части статистики
        is_itf_tournament = tournament_name and "itf" in tournament_name.lower()
        if is_itf_tournament:
            # Проверяем наличие хотя бы одной метрики статистики
            has_any_stats = (
                (points and not math.isnan(points[0]) and not math.isnan(points[1]))
                or (breakpoints_won and not math.isnan(breakpoints_won[0]) and not math.isnan(breakpoints_won[1]))
                or (service_points_won and not math.isnan(service_points_won[0]) and not math.isnan(service_points_won[1]))
            )
            # Для ITF также требуем явное преимущество в счете (выигран сет или разница 3+ гейма)
            has_score_advantage = abs(set_diff) > 0 or abs(game_diff) >= 3
            if not (has_any_stats or has_score_advantage):
                continue  # Пропускаем ITF матчи без статистики и без явного преимущества

        # points_won теперь опциональный - если нет, используем другие метрики
        points_diff = 0.0
        has_points = points and not math.isnan(points[0]) and not math.isnan(points[1])
        if has_points:
            points_diff = points[leader_index] - points[trailing_index]
            if points_diff < 4:
                continue
        else:
            # Если нет points_won, требуем хотя бы минимальное преимущество по сетам/геймам
            # Ослабляем критерий: если выигран сет, достаточно разницы 2+ гейма
            # Если сетов равное количество, требуется разница 3+ гейма
            if abs(set_diff) == 0:
                if abs(game_diff) < 3:
                    continue
            elif abs(set_diff) == 1:
                # Выигран один сет - достаточно разницы 2+ гейма в текущем сете
                if abs(game_diff) < 2:
                    continue

        breaks_diff = 0.0
        has_breaks = breakpoints_won and not math.isnan(breakpoints_won[0]) and not math.isnan(breakpoints_won[1])
        if has_breaks:
            breaks_diff = breakpoints_won[leader_index] - breakpoints_won[trailing_index]
            # Если есть points_won, breaks_diff должен быть >= 0
            # Если нет points_won, но есть преимущество в счете, разрешаем breaks_diff >= -1
            if has_points and breaks_diff < 0:
                continue
            elif not has_points and breaks_diff < -1:
                continue

        service_diff = 0.0
        if (
            service_points_won
            and not math.isnan(service_points_won[0])
            and not math.isnan(service_points_won[1])
        ):
            service_diff = service_points_won[leader_index] - service_points_won[trailing_index]

        games_advantage = set_diff * 6 + (game_diff if leader_index == 0 else -game_diff)
        
        # Если нет points_won, увеличиваем вес преимущества в счете
        if has_points:
            dominance_score = (
                games_advantage * 2
                + max(points_diff, 0) * 0.6
                + max(breaks_diff, 0) * 4
                + max(service_diff, 0) * 0.4
            )
        else:
            # Без points_won - больше веса на счет и breaks
            dominance_score = (
                games_advantage * 3  # Увеличиваем вес преимущества в счете
                + max(breaks_diff, 0) * 5  # Увеличиваем вес breaks
                + max(service_diff, 0) * 0.5
            )

        # Проверяем, что dominance_score валидный (не nan)
        if math.isnan(dominance_score) or math.isinf(dominance_score) or dominance_score <= 0:
            continue

        # Additional guardrail: skip very early matches
        # Ослабляем: если есть преимущество в счете (выигран сет или разница 3+ гейма), разрешаем
        if total_games_played < 6 and max(sets_home, sets_away) == 0:
            # Если разница в геймах >= 3, разрешаем даже при малом количестве геймов
            if abs(game_diff) < 3:
                continue

        teams = details.get("teams") or []
        if len(teams) < 2:
            continue
        player_home = teams[0].get("name")
        player_away = teams[1].get("name")
        if not player_home or not player_away:
            continue

        analyzed.append(
            {
                "sport": "tennis",
                "slug": slug,
                "teams": [player_home.strip(), player_away.strip()],
                "status_code": status_code,
                "sets_score": f"{sets_home}:{sets_away}",
                "current_set": current_set_index,
                "current_games": current_games,
                "total_games_played": total_games_played,
                "leader_index": leader_index,
                "dominance_score": dominance_score,
                "points": points,
                "points_diff": points_diff,
                "service_points_won": service_points_won,
                "service_diff": service_diff,
                "breakpoints_won": breakpoints_won,
                "total_breakpoints": total_breakpoints,
                "breaks_diff": breaks_diff,
                "aces": stats_map.get("aces"),
                "double_faults": stats_map.get("double_faults"),
                "tournament": (details.get("unique_tournament") or {}).get("name")
                or details.get("tournament_name"),
                "country": (details.get("country") or {}).get("name"),
            }
        )

    return analyzed

