from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

from scores24_graphql_client import fetch_live_matches, fetch_match_stats


LOWER_DIVISION_KEYWORDS = [
    "лига 2",
    "лига два",
    "ligue 2",
    "вторая лига",
    "серия b",
    "serie b",
    "segunda",
    "segunda division",
    "segunda liga",
    "liga 2",
    "liga2",
    "league two",
    "championship",
    "чемпионшип",
    "1-я лига",
    "первая лига",
    "второй дивизион",
    "second division",
    "liga pro",
    "примера b",
    "national league",
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
    "лига чемпионов",
    "champions league",
    "лига европы",
    "europa league",
    "conference league",
    "лига конференций",
    "кубок страны",
    "кубок англии",
    "fa cup",
    "efl cup",
    "carabao cup",
    "кубок италии",
    "coppa italia",
    "copa del rey",
    "короля",
    "кубок германии",
    "dfb pokal",
    "кубок франции",
    "copa libertadores",
    "copa sudamericana",
    "club world cup",
    "world cup",
    "чемпионат мира",
    "кубок азии",
    "asian cup",
    "copa america",
    "africa cup",
    "кубок африки",
    "euro",
    "евро",
    "uefa nations league",
    "nations league",
]


def _normalize(text: Optional[str]) -> str:
    if not text:
        return ""
    return " ".join(text.lower().split())


def _is_tournament_allowed(name: Optional[str]) -> bool:
    normalized = _normalize(name)
    if not normalized:
        return True

    # СНАЧАЛА проверяем запрещенные ключевые слова (молодежка, женский футбол и т.д.)
    # Это важно, чтобы молодежные турниры с "евро" не проходили
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


MINIMUM_MINUTE_THRESHOLD = 15  # Уменьшено с 18 до 15 минут для большего охвата


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


def _parse_score(details: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    game_state = details.get("game_state") or {}
    home_score = game_state.get("home_score")
    away_score = game_state.get("away_score")
    if home_score is not None and away_score is not None:
        try:
            return int(home_score), int(away_score)
        except ValueError:
            pass

    def _from_string(value: Optional[str]) -> Optional[Tuple[int, int]]:
        if not value:
            return None
        for separator in (":", "-", " "):
            if separator in value:
                parts = value.replace(" ", "").split(separator)
                if len(parts) == 2 and all(p.isdigit() for p in parts):
                    return int(parts[0]), int(parts[1])
        return None

    score = _from_string(details.get("result_score"))
    if score:
        return score

    for entry in details.get("result_scores") or []:
        score = _from_string(entry.get("value"))
        if score:
            return score

    return None


def _extract_totals(statistic: Optional[Dict[str, Any]]) -> Dict[str, Tuple[Optional[float], Optional[float]]]:
    totals: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
    if not statistic:
        return totals
    for period in statistic.get("periods") or []:
        if period.get("type") != "total":
            continue
        for group in period.get("groups") or []:
            for item in group.get("items") or []:
                item_type = item.get("type")
                if not item_type:
                    continue
                team1_value = _parse_numeric(item.get("team1_value"))
                team2_value = _parse_numeric(item.get("team2_value"))
                totals[item_type] = (team1_value, team2_value)
    return totals


def _extract_positions(details: Dict[str, Any]) -> Dict[str, Optional[int]]:
    positions: Dict[str, Optional[int]] = {}
    for standing in details.get("standings") or []:
        team = standing.get("team") or {}
        name = team.get("name")
        position_raw = standing.get("position_total") or standing.get("position_home") or standing.get("position_away")
        if name and position_raw:
            try:
                positions[name] = int(position_raw)
            except ValueError:
                continue
    return positions


def _parse_minute_value(value: Optional[Any]) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "—"}:
        return None
    match = re.match(r"(\d+)", text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def analyze_live_matches(limit: int = 30) -> List[Dict[str, Any]]:
    live_matches = fetch_live_matches(limit)
    analyzed: List[Dict[str, Any]] = []

    for match_info in live_matches:
        slug = match_info["slug"]
        try:
            details = fetch_match_stats(slug)
        except Exception:
            continue

        score = _parse_score(details)
        if not score:
            continue
        home_score, away_score = score
        if home_score == away_score:
            continue

        totals = _extract_totals(details.get("statistic"))
        xg = totals.get("xg")
        possession = totals.get("ball_possession")
        shots_total = totals.get("shots_total")
        shots_on_target = totals.get("shots_on_target") or totals.get("shots_on_goal")

        # Ослабленные требования: possession ИЛИ shots_on_target (хотя бы одно)
        # Это увеличит количество анализируемых матчей
        has_possession = possession and possession[0] is not None and possession[1] is not None
        has_shots = shots_on_target and shots_on_target[0] is not None and shots_on_target[1] is not None
        
        if not (has_possession or has_shots):
            continue

        teams = details.get("teams") or []
        if len(teams) < 2:
            continue

        raw_minute = details.get("minute")
        if raw_minute is None:
            raw_minute = match_info.get("minute")
        minute_str = str(raw_minute) if raw_minute is not None else ""
        minute_numeric = _parse_minute_value(details.get("minute"))
        if minute_numeric is None:
            minute_numeric = _parse_minute_value(match_info.get("minute"))
        if minute_numeric is not None and minute_numeric < MINIMUM_MINUTE_THRESHOLD:
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

        positions = _extract_positions(details)
        status_code = (
            (details.get("status") or {}).get("code")
            or (match_info.get("status") or {}).get("code")
        )

        def _leader_value(metric: Tuple[Optional[float], Optional[float]]) -> float:
            if metric is None:
                return math.nan
            value = metric[leader_index]
            return float(value) if value is not None else math.nan

        def _trailing_value(metric: Tuple[Optional[float], Optional[float]]) -> float:
            if metric is None:
                return math.nan
            value = metric[trailing_index]
            return float(value) if value is not None else math.nan

        leader_metrics = {
            "xg": _leader_value(xg) if xg else math.nan,
            "possession": _leader_value(possession),
            "shots_total": _leader_value(shots_total) if shots_total else math.nan,
            "shots_on_target": _leader_value(shots_on_target),
        }
        trailing_metrics = {
            "xg": _trailing_value(xg) if xg else math.nan,
            "possession": _trailing_value(possession),
            "shots_total": _trailing_value(shots_total) if shots_total else math.nan,
            "shots_on_target": _trailing_value(shots_on_target),
        }

        # xG и shots_total опциональные - если есть, используем, если нет - только другие метрики
        xg_component = 0.0
        if xg and xg[0] is not None and xg[1] is not None:
            xg_component = (leader_metrics["xg"] - trailing_metrics["xg"]) * 3
        
        shots_total_component = 0.0
        if shots_total and shots_total[0] is not None and shots_total[1] is not None:
            shots_total_component = (leader_metrics["shots_total"] - trailing_metrics["shots_total"])
        
        # Учитываем время матча и текущий счет
        time_factor = 1.0
        if minute_numeric is not None and minute_numeric > 0:
            time_factor = minute_numeric / 90.0  # 0.22 для 20-й минуты, 0.89 для 80-й
        
        # Учитываем текущий счет (разница голов)
        score_diff = abs(home_score - away_score)
        score_factor = score_diff * 2  # 1:0 = 2, 2:0 = 4, 3:0 = 6
        
        # Улучшенная формула с учетом времени и счета
        # Проверяем на math.nan перед использованием
        shots_on_target_diff = 0.0
        if not math.isnan(leader_metrics["shots_on_target"]) and not math.isnan(trailing_metrics["shots_on_target"]):
            shots_on_target_diff = (leader_metrics["shots_on_target"] - trailing_metrics["shots_on_target"]) * 2
        
        possession_diff = 0.0
        if not math.isnan(leader_metrics["possession"]) and not math.isnan(trailing_metrics["possession"]):
            possession_diff = (leader_metrics["possession"] - trailing_metrics["possession"]) * 0.5
        
        dominance_score = (
            xg_component
            + shots_on_target_diff
            + shots_total_component
            + possession_diff
            + score_factor * time_factor  # Учитываем счет и время матча
        )
        
        # Проверяем, что dominance_score валидный (не nan)
        if math.isnan(dominance_score) or math.isinf(dominance_score):
            continue  # Пропускаем матч с невалидным dominance_score

        has_xg = xg is not None and xg[0] is not None and xg[1] is not None
        
        analyzed.append(
            {
                "slug": slug,
                "tournament": tournament,
                "country": country_name,
                "minute": minute_str,
                "minute_numeric": minute_numeric,
                "teams": [home_name, away_name],
                "score": f"{home_score}:{away_score}",
                "home_score": home_score,
                "away_score": away_score,
                "leader_index": leader_index,
                "status_code": status_code,
                "xg": xg,
                "has_xg": has_xg,
                "possession": possession,
                "shots_total": shots_total,
                "shots_on_target": shots_on_target,
                "positions": positions,
                "leader_metrics": leader_metrics,
                "trailing_metrics": trailing_metrics,
                "dominance_score": dominance_score,
            }
        )

    return analyzed


if __name__ == "__main__":
    matches = analyze_live_matches()
    print(f"Collected {len(matches)} matches with full statistics")
    for idx, match in enumerate(matches, 1):
        leader = match["teams"][match["leader_index"]]
        print(
            f"[{idx}] {match['teams'][0]} vs {match['teams'][1]} — {match['score']} ({match['minute']}') "
            f"xG {match['xg'][0]:.2f}-{match['xg'][1]:.2f}, shotsOT {match['shots_on_target'][0]:.0f}-"
            f"{match['shots_on_target'][1]:.0f}, possession {match['possession'][0]:.0f}-{match['possession'][1]:.0f} "
            f"leader: {leader}"
        )

