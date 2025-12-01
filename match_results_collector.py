#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматический сбор результатов матчей с scores24.com.
Проверяет завершенные матчи и обновляет результаты в базе данных.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from zoneinfo import ZoneInfo

from scores24_graphql_client import fetch_match_stats
from statistics_tracker import get_tracker, MatchResult
from enhanced_data_collector import get_enhanced_collector
from team_player_database import get_database
from team_data_collector import update_team_from_finished_match

TZ_MOSCOW = ZoneInfo("Europe/Moscow")
DATA_DIR = Path("data")
ENHANCED_PREDICTIONS_LOG = DATA_DIR / "enhanced_predictions.jsonl"
PREDICTIONS_LOG = DATA_DIR / "predictions_log.jsonl"

# Статусы завершенных матчей (из GraphQL API)
# Для футбола: 3=Завершен, 4=Отменен, 5=Перенесен, 6=Прерван
# Для тенниса: 100=Завершен
FINISHED_STATUS_CODES = {"3", "4", "5", "6", "100"}  # Завершен, Отменен, Перенесен, Прерван, Завершен (теннис)
PENDING_STATUS_CODES = {"1", "2", "7"}  # Не начат, Идет, Перерыв


def load_pending_predictions() -> List[Dict]:
    """Загружает все прогнозы со статусом pending"""
    predictions = []
    
    # Загружаем из enhanced_predictions
    if ENHANCED_PREDICTIONS_LOG.exists():
        try:
            with ENHANCED_PREDICTIONS_LOG.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if data.get("result") == "pending":
                            predictions.append(data)
        except Exception as e:
            print(f"Error loading enhanced predictions: {e}")
    
    return predictions


def get_match_result_from_status(
    match_data: Dict,
    predicted_side: str,
    leader_index: int,
    sport: str = "soccer"
) -> Optional[str]:
    """
    Определяет результат матча на основе финального счета.
    
    Args:
        match_data: Данные матча из GraphQL API
        predicted_side: Предсказанная сторона (П1 или П2)
        leader_index: Индекс лидера (0 для home, 1 для away)
        sport: Вид спорта (soccer, tennis, etc.)
    
    Returns:
        "win", "loss" или None (если не удалось определить)
    """
    status_code = str(match_data.get("status", {}).get("code", ""))
    
    # Если матч не завершен, возвращаем None
    if status_code not in FINISHED_STATUS_CODES:
        return None
    
    # Если матч отменен или прерван, считаем cancelled
    if status_code in {"4", "6"}:  # Отменен, Прерван
        return "cancelled"
    
    # Для тенниса используем result_score
    if sport == "tennis":
        result_score = match_data.get("result_score", "")
        if not result_score:
            return None
        
        # Парсим счет типа "2:0" или "2:1"
        try:
            scores = result_score.split(":")
            home_sets = int(scores[0])
            away_sets = int(scores[1])
            
            # Определяем победителя
            if home_sets > away_sets:
                winner_index = 0  # Home победил
            elif away_sets > home_sets:
                winner_index = 1  # Away победил
            else:
                return None  # Не должно быть ничьей в теннисе
            
        except (ValueError, IndexError):
            return None
    else:
        # Для футбола и других видов спорта используем game_state
        game_state = match_data.get("game_state", {})
        home_score = game_state.get("home_score", 0)
        away_score = game_state.get("away_score", 0)
        
        if home_score is None or away_score is None:
            return None
        
        # Определяем победителя
        if home_score > away_score:
            winner_index = 0  # Home победил
        elif away_score > home_score:
            winner_index = 1  # Away победил
        else:
            # Ничья - это проигрыш для нас (мы ставим на победу)
            return "loss"
    
    # Сравниваем с предсказанием
    # predicted_side: "П1" означает home (index 0), "П2" означает away (index 1)
    predicted_index = 0 if predicted_side == "П1" else 1
    
    if winner_index == predicted_index:
        return "win"
    else:
        return "loss"


def check_match_result(
    match_slug: str,
    sport: str,
    predicted_side: str,
    leader_index: int,
    max_retries: int = 3
) -> Optional[Dict]:
    """
    Проверяет результат матча по slug.
    
    Returns:
        Dict с результатом или None если матч еще не завершен
    """
    for attempt in range(max_retries):
        try:
            match_data = fetch_match_stats(match_slug, sport)
            
            status_code = match_data.get("status", {}).get("code", "")
            
            # Если матч еще не завершен
            if status_code in PENDING_STATUS_CODES:
                return None
            
            # Если матч завершен, определяем результат
            if status_code in FINISHED_STATUS_CODES:
                result = get_match_result_from_status(
                    match_data,
                    predicted_side,
                    leader_index
                )
                
                game_state = match_data.get("game_state", {})
                final_score = f"{game_state.get('home_score', 0)}:{game_state.get('away_score', 0)}"
                
                return {
                    "result": result,
                    "final_score": final_score,
                    "status_code": status_code,
                    "match_data": match_data
                }
            
            # Неизвестный статус
            return None
            
        except Exception as e:
            print(f"Error checking match {match_slug} (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Экспоненциальная задержка
            else:
                print(f"Failed to check match {match_slug} after {max_retries} attempts")
                return None
    
    return None


def update_team_from_finished_match(
    match_data: Dict,
    sport: str,
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
    tournament: str,
    country: str
):
    """Обновляет статистику команд на основе завершенного матча"""
    database = get_database()
    
    # Определяем результаты
    if home_score > away_score:
        home_result = "win"
        away_result = "loss"
    elif away_score > home_score:
        home_result = "loss"
        away_result = "win"
    else:
        home_result = "draw"
        away_result = "draw"
    
    # Обновляем статистику команд
    if sport in ["football", "basketball", "handball"]:
        database.update_team_from_match(
            team_name=home_team,
            sport=sport,
            league=tournament,
            country=country,
            is_home=True,
            goals_for=home_score,
            goals_against=away_score,
            result=home_result
        )
        
        database.update_team_from_match(
            team_name=away_team,
            sport=sport,
            league=tournament,
            country=country,
            is_home=False,
            goals_for=away_score,
            goals_against=home_score,
            result=away_result
        )
    elif sport == "tennis":
        database.update_player_from_match(
            player_name=home_team,
            opponent_name=away_team,
            sport="tennis",
            result=home_result
        )
        
        database.update_player_from_match(
            player_name=away_team,
            opponent_name=home_team,
            sport="tennis",
            result=away_result
        )


def update_prediction_result(
    prediction: Dict,
    result_data: Dict
) -> bool:
    """Обновляет результат прогноза в базе данных"""
    match_id = prediction.get("match_id")
    if not match_id:
        return False
    
    result = result_data.get("result")
    if not result:
        return False
    
    # Обновляем в обычном трекере
    tracker = get_tracker()
    match_result = MatchResult.WIN if result == "win" else (
        MatchResult.LOSS if result == "loss" else MatchResult.CANCELLED
    )
    
    notes = f"Final score: {result_data.get('final_score', 'N/A')}"
    updated_tracker = tracker.update_result(match_id, match_result, notes)
    
    # Обновляем в расширенном сборщике
    enhanced_collector = get_enhanced_collector()
    updated_enhanced = enhanced_collector.update_result(match_id, result, notes)
    
    # ОБНОВЛЯЕМ ИСТОРИЧЕСКИЕ ДАННЫЕ КОМАНД
    try:
        match_data = result_data.get("match_data")
        if match_data and result != "cancelled":
            sport = prediction.get("sport_type", "football")
            teams = prediction.get("teams", "").split(" - ")
            if len(teams) >= 2:
                home_team = teams[0].strip()
                away_team = teams[1].strip()
                
                game_state = match_data.get("game_state", {})
                home_score = game_state.get("home_score", 0) or 0
                away_score = game_state.get("away_score", 0) or 0
                
                tournament = match_data.get("tournament_name") or match_data.get("unique_tournament", {}).get("name", "")
                country = match_data.get("country", {})
                if isinstance(country, dict):
                    country = country.get("name", "")
                else:
                    country = str(country) if country else ""
                
                update_team_from_finished_match(
                    match_data=match_data,
                    sport=sport,
                    home_team=home_team,
                    away_team=away_team,
                    home_score=home_score,
                    away_score=away_score,
                    tournament=tournament,
                    country=country
                )
    except Exception as e:
        print(f"Warning: Failed to update team history: {e}")
    
    return updated_tracker or updated_enhanced


def collect_results_for_pending_matches(
    max_matches: int = 50,
    sport: str = "soccer"
) -> Dict[str, int]:
    """
    Собирает результаты для всех pending прогнозов.
    
    Returns:
        Dict с статистикой обновлений
    """
    print(f"Starting results collection for {sport}...")
    
    # Загружаем pending прогнозы
    predictions = load_pending_predictions()
    
    # Фильтруем по виду спорта
    sport_mapping = {
        "football": "soccer",
        "tennis": "tennis",
        "basketball": "basketball",
        "handball": "handball",
    }
    graphql_sport = sport_mapping.get(sport, "soccer")
    
    filtered_predictions = [
        p for p in predictions
        if p.get("sport_type") == sport
    ][:max_matches]
    
    print(f"Found {len(filtered_predictions)} pending predictions for {sport}")
    
    stats = {
        "checked": 0,
        "updated": 0,
        "still_pending": 0,
        "errors": 0
    }
    
    for pred in filtered_predictions:
        match_id = pred.get("match_id")
        match_slug = match_id  # В нашей системе match_id = slug
        predicted_side = pred.get("bet_side", "П1")
        
        # Определяем leader_index из predicted_side
        leader_index = 0 if predicted_side == "П1" else 1
        
        stats["checked"] += 1
        
        try:
            result_data = check_match_result(
                match_slug,
                graphql_sport,
                predicted_side,
                leader_index
            )
            
            if result_data and result_data.get("result"):
                # Матч завершен, обновляем результат
                if update_prediction_result(pred, result_data):
                    stats["updated"] += 1
                    print(f"[OK] Updated {match_id}: {result_data.get('result')} (score: {result_data.get('final_score')})")
                else:
                    stats["errors"] += 1
                    print(f"[ERROR] Failed to update {match_id}")
            else:
                # Матч еще не завершен
                stats["still_pending"] += 1
                
        except Exception as e:
            stats["errors"] += 1
            print(f"[ERROR] Error processing {match_id}: {e}")
        
        # Небольшая задержка между запросами
        time.sleep(0.5)
    
    print(f"\nResults collection completed:")
    print(f"  Checked: {stats['checked']}")
    print(f"  Updated: {stats['updated']}")
    print(f"  Still pending: {stats['still_pending']}")
    print(f"  Errors: {stats['errors']}")
    
    return stats


def main():
    """Основная функция для периодического сбора результатов"""
    sports = ["football", "tennis", "basketball", "handball"]
    
    all_stats = {}
    for sport in sports:
        stats = collect_results_for_pending_matches(max_matches=50, sport=sport)
        all_stats[sport] = stats
    
    return all_stats


if __name__ == "__main__":
    main()

