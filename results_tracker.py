#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система учета результатов ставок
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from zoneinfo import ZoneInfo

DATA_DIR = Path("data")
RESULTS_FILE = DATA_DIR / "bet_results.csv"

RESULTS_HEADER = [
    "date",
    "timestamp_msk",
    "sport",
    "tournament",
    "home_team",
    "away_team",
    "bet_outcome",  # П1, П2
    "coefficient",
    "stake_rub",
    "payout_rub",
    "profit_rub",
    "roi_percent",
    "ticket_id",
    "match_time",
    "score_at_bet",
    "final_score",
    "result_status",  # win, loss, void
    "notes",
]

def _ensure_results_file():
    """Создает файл результатов, если его нет."""
    if not RESULTS_FILE.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with RESULTS_FILE.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            writer.writerow(RESULTS_HEADER)

def add_result(
    sport: str,
    tournament: str,
    home_team: str,
    away_team: str,
    bet_outcome: str,  # П1 или П2
    coefficient: float,
    stake_rub: float,
    payout_rub: Optional[float] = None,
    ticket_id: Optional[str] = None,
    match_time: Optional[str] = None,
    score_at_bet: Optional[str] = None,
    final_score: Optional[str] = None,
    result_status: str = "win",  # win, loss, void
    notes: Optional[str] = None,
):
    """Добавляет результат ставки в базу."""
    _ensure_results_file()
    
    now = datetime.now(ZoneInfo("Europe/Moscow"))
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    if payout_rub is None:
        payout_rub = stake_rub * coefficient
    
    profit_rub = payout_rub - stake_rub
    roi_percent = (profit_rub / stake_rub) * 100 if stake_rub > 0 else 0
    
    row = [
        date_str,
        timestamp_str,
        sport,
        tournament,
        home_team,
        away_team,
        bet_outcome,
        f"{coefficient:.2f}",
        f"{stake_rub:.2f}",
        f"{payout_rub:.2f}",
        f"{profit_rub:.2f}",
        f"{roi_percent:.2f}",
        ticket_id or "",
        match_time or "",
        score_at_bet or "",
        final_score or "",
        result_status,
        notes or "",
    ]
    
    with RESULTS_FILE.open("a", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerow(row)

def get_statistics(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Получает статистику по результатам."""
    if not RESULTS_FILE.exists():
        return {
            "total_bets": 0,
            "wins": 0,
            "losses": 0,
            "voids": 0,
            "win_rate": 0.0,
            "total_stake": 0.0,
            "total_payout": 0.0,
            "total_profit": 0.0,
            "roi": 0.0,
            "by_sport": {},
        }
    
    total_bets = 0
    wins = 0
    losses = 0
    voids = 0
    total_stake = 0.0
    total_payout = 0.0
    by_sport: Dict[str, Dict[str, Any]] = {}
    
    with RESULTS_FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row.get("date", "")
            if start_date and date < start_date:
                continue
            if end_date and date > end_date:
                continue
            
            total_bets += 1
            status = row.get("result_status", "").lower()
            if status == "win":
                wins += 1
            elif status == "loss":
                losses += 1
            else:
                voids += 1
            
            try:
                stake = float(row.get("stake_rub", 0))
                payout = float(row.get("payout_rub", 0))
                total_stake += stake
                total_payout += payout
            except (ValueError, TypeError):
                pass
            
            sport = row.get("sport", "unknown")
            if sport not in by_sport:
                by_sport[sport] = {
                    "bets": 0,
                    "wins": 0,
                    "losses": 0,
                    "stake": 0.0,
                    "payout": 0.0,
                    "profit": 0.0,
                }
            
            by_sport[sport]["bets"] += 1
            if status == "win":
                by_sport[sport]["wins"] += 1
            elif status == "loss":
                by_sport[sport]["losses"] += 1
            
            try:
                by_sport[sport]["stake"] += stake
                by_sport[sport]["payout"] += payout
                by_sport[sport]["profit"] += (payout - stake)
            except (ValueError, TypeError):
                pass
    
    total_profit = total_payout - total_stake
    win_rate = (wins / total_bets * 100) if total_bets > 0 else 0.0
    roi = (total_profit / total_stake * 100) if total_stake > 0 else 0.0
    
    # Рассчитываем win rate для каждого вида спорта
    for sport_data in by_sport.values():
        total = sport_data["bets"]
        if total > 0:
            sport_data["win_rate"] = (sport_data["wins"] / total * 100)
        else:
            sport_data["win_rate"] = 0.0
    
    return {
        "total_bets": total_bets,
        "wins": wins,
        "losses": losses,
        "voids": voids,
        "win_rate": win_rate,
        "total_stake": total_stake,
        "total_payout": total_payout,
        "total_profit": total_profit,
        "roi": roi,
        "by_sport": by_sport,
    }

