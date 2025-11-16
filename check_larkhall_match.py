#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_live_analyzer import analyze_live_matches
from generate_live_report import _get_leader_odds

PRIMARY_MAX_ODDS = 1.85
EXTENDED_MAX_ODDS = 2.00
EXTENDED_MIN_DOMINANCE = 10.0
EXTENDED_MIN_XG_DIFF = 0.35
EXTENDED_MIN_SOT_DIFF = 2

matches = analyze_live_matches(limit=100)
larkhall = [m for m in matches if "ларкхалл" in str(m.get("teams", [])).lower() or "larkhall" in str(m.get("teams", [])).lower()]

if larkhall:
    m = larkhall[0]
    teams = m.get("teams", ["?", "?"])
    score = m.get("score", "?")
    dominance = m.get("dominance_score", 0)
    slug = m.get("slug", "")
    leader_idx = m.get("leader_index", 0)
    
    odds = _get_leader_odds(slug, leader_idx)
    leader = m.get("leader_metrics", {})
    trailing = m.get("trailing_metrics", {})
    xg_diff = leader.get("xg", 0) - trailing.get("xg", 0)
    sot_diff = leader.get("shots_on_target", 0) - trailing.get("shots_on_target", 0)
    
    print(f"Матч: {teams[0]} vs {teams[1]}")
    print(f"Счет: {score}")
    print(f"Dominance: {dominance:.1f}")
    print(f"Кэф: {odds.value if odds.value else 'НЕТ'}")
    print(f"xG разница: {xg_diff:.2f}")
    print(f"Удары в створ разница: {sot_diff}")
    print()
    
    if odds.value is None:
        print("[FILTERED] Нет коэффициентов")
    elif odds.value <= PRIMARY_MAX_ODDS:
        print(f"[OK] Primary tier (кэф <= {PRIMARY_MAX_ODDS})")
    elif odds.value <= EXTENDED_MAX_ODDS:
        print(f"[CHECK] Extended tier (кэф <= {EXTENDED_MAX_ODDS})")
        print(f"  - Dominance >= {EXTENDED_MIN_DOMINANCE}? {dominance >= EXTENDED_MIN_DOMINANCE} ({dominance:.1f})")
        print(f"  - xG diff >= {EXTENDED_MIN_XG_DIFF}? {xg_diff >= EXTENDED_MIN_XG_DIFF} ({xg_diff:.2f})")
        print(f"  - SOT diff >= {EXTENDED_MIN_SOT_DIFF}? {sot_diff >= EXTENDED_MIN_SOT_DIFF} ({sot_diff})")
        
        if (dominance >= EXTENDED_MIN_DOMINANCE and 
            xg_diff >= EXTENDED_MIN_XG_DIFF and 
            sot_diff >= EXTENDED_MIN_SOT_DIFF):
            print("[OK] Проходит extended критерии!")
        else:
            print("[FILTERED] Не проходит extended критерии")
    else:
        print(f"[FILTERED] Кэф слишком высокий: {odds.value:.2f} > {EXTENDED_MAX_ODDS}")
else:
    print("Матч Ларкхалл не найден")

