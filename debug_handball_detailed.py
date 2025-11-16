#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Детальная отладка гандбола"""

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_handball_analyzer import _parse_minute, _parse_int, _parse_score, _is_allowed_handball_tournament
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

all_handball = fetch_live_matches(limit=30, sport="handball")

reasons = {
    "tournament": 0,
    "no_score": 0,
    "low_total": 0,
    "draw": 0,
    "low_diff": 0,
    "no_statistic": 0,
    "passed": 0
}

for match_info in all_handball:
    slug = match_info["slug"]
    teams = match_info.get("teams", [])
    home = teams[0].get("name", "?") if teams else "?"
    away = teams[1].get("name", "?") if len(teams) > 1 else "?"
    
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
        reasons["tournament"] += 1
        continue
    
    game_state = details.get("game_state") or {}
    home_score = _parse_int(game_state.get("home_score"))
    away_score = _parse_int(game_state.get("away_score"))
    if home_score is None or away_score is None:
        parsed = _parse_score(details.get("result_score"))
        if not parsed:
            reasons["no_score"] += 1
            continue
        home_score, away_score = parsed
    
    total_score = home_score + away_score
    
    minute_numeric = _parse_minute(details.get("minute") or match_info.get("minute"))
    if minute_numeric is None:
        estimated_minute = min(total_score, 50)
        if estimated_minute < 25:
            reasons["low_total"] += 1
            continue
        minute_numeric = estimated_minute
    
    if total_score < 25:
        reasons["low_total"] += 1
        if reasons["low_total"] <= 3:
            print(f"LOW_TOTAL: {home} vs {away} - {home_score}:{away_score} (тотал {total_score})")
        continue
    
    if home_score == away_score:
        reasons["draw"] += 1
        if reasons["draw"] <= 3:
            print(f"DRAW: {home} vs {away} - {home_score}:{away_score}")
        continue
    
    score_diff = abs(home_score - away_score)
    diff_threshold = 3 if minute_numeric >= 45 else 4
    if score_diff < diff_threshold:
        reasons["low_diff"] += 1
        if reasons["low_diff"] <= 5:
            print(f"LOW_DIFF: {home} vs {away} - {home_score}:{away_score} (разница {score_diff}, нужно ≥{diff_threshold}, минута {minute_numeric})")
        continue
    
    if details.get("statistic") and not details["statistic"].get("periods"):
        reasons["no_statistic"] += 1
        continue
    
    reasons["passed"] += 1
    print(f"✅ PASSED: {home} vs {away} - {home_score}:{away_score} ({minute_numeric}') | разница {score_diff} | тотал {total_score}")

print(f"\nИТОГИ:")
for key, value in reasons.items():
    print(f"  {key}: {value}")

