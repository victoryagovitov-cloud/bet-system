#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches
from graphql_basketball_analyzer import _parse_minute_value

all_matches = fetch_live_matches(limit=50, sport="basketball")
print(f"Всего матчей: {len(all_matches)}\n")

matches_after_15 = []
for match in all_matches:
    minute_str = match.get("minute", "")
    minute_numeric = _parse_minute_value(minute_str)
    
    if minute_numeric and minute_numeric >= 15:
        teams = match.get("teams", [])
        home = teams[0].get("name", "?") if len(teams) > 0 else "?"
        away = teams[1].get("name", "?") if len(teams) > 1 else "?"
        matches_after_15.append((home, away, minute_numeric, minute_str))

print(f"Матчей после 15 минут: {len(matches_after_15)}\n")

if len(matches_after_15) > 0:
    print("Матчи после 15 минут:")
    for home, away, minute_num, minute_str in matches_after_15:
        print(f"  {home} - {away}: {minute_str} ({minute_num} минут)")
else:
    print("Нет матчей после 15 минут - все матчи слишком рано")

