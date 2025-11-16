#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Проверка всех live матчей и причин отсева"""

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_live_analyzer import analyze_live_matches
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 60)
print("ПРОВЕРКА ВСЕХ LIVE МАТЧЕЙ")
print("=" * 60)

# Получаем все live матчи
all_live = fetch_live_matches(limit=100)
print(f"\n📊 Всего live матчей найдено: {len(all_live)}")

# Показываем первые 20
print("\n🔍 Первые 20 live матчей:")
for i, match in enumerate(all_live[:20], 1):
    teams = match.get("teams", [])
    home = teams[0].get("name", "?") if teams else "?"
    away = teams[1].get("name", "?") if len(teams) > 1 else "?"
    score = match.get("game_score", "?")
    minute = match.get("minute", "?")
    tournament = match.get("tournament_name", "?")
    print(f"{i}. {home} vs {away} - {score} ({minute}') | {tournament}")

# Анализируем с полной статистикой
print("\n" + "=" * 60)
print("АНАЛИЗ С ПОЛНОЙ СТАТИСТИКОЙ")
print("=" * 60)

analyzed = analyze_live_matches(limit=100)
print(f"\n✅ Матчей с полной статистикой и неничейным счетом: {len(analyzed)}")

if analyzed:
    print("\n📋 Найденные матчи:")
    for i, match in enumerate(analyzed[:10], 1):
        teams = match["teams"]
        score = match["score"]
        minute = match["minute"]
        tournament = match.get("tournament", "?")
        dominance = match.get("dominance_score", 0)
        print(f"\n{i}. {teams[0]} vs {teams[1]}")
        print(f"   Счет: {score} ({minute}')")
        print(f"   Турнир: {tournament}")
        print(f"   Dominance score: {dominance:.2f}")
        print(f"   xG: {match['xg'][0]:.2f} - {match['xg'][1]:.2f}")
        print(f"   Удары в створ: {match['shots_on_target'][0]:.0f} - {match['shots_on_target'][1]:.0f}")
else:
    print("\n❌ Нет матчей, прошедших базовую фильтрацию")

# Проверяем причины отсева
print("\n" + "=" * 60)
print("АНАЛИЗ ПРИЧИН ОТСЕВА")
print("=" * 60)

reasons = {
    "no_stats": 0,
    "draw_score": 0,
    "missing_metrics": 0,
    "too_early": 0,
    "low_division": 0,
    "total": 0
}

for match_info in all_live[:50]:
    reasons["total"] += 1
    slug = match_info["slug"]
    
    try:
        details = fetch_match_stats(slug)
    except Exception as e:
        reasons["no_stats"] += 1
        continue
    
    # Проверяем счет
    from graphql_live_analyzer import _parse_score
    score = _parse_score(details)
    if not score:
        continue
    home_score, away_score = score
    if home_score == away_score:
        reasons["draw_score"] += 1
        continue
    
    # Проверяем метрики
    from graphql_live_analyzer import _extract_totals, _parse_minute_value, _is_tournament_allowed
    totals = _extract_totals(details.get("statistic"))
    xg = totals.get("xg")
    possession = totals.get("ball_possession")
    shots_total = totals.get("shots_total")
    shots_on_target = totals.get("shots_on_target") or totals.get("shots_on_goal")
    
    if not all(metric and metric[0] is not None and metric[1] is not None for metric in (xg, possession, shots_total, shots_on_target)):
        reasons["missing_metrics"] += 1
        continue
    
    # Проверяем минуту
    minute_numeric = _parse_minute_value(details.get("minute"))
    if minute_numeric is None:
        minute_numeric = _parse_minute_value(match_info.get("minute"))
    if minute_numeric is not None and minute_numeric < 23:
        reasons["too_early"] += 1
        continue
    
    # Проверяем турнир
    tournament = (
        (details.get("unique_tournament") or {}).get("name")
        or details.get("tournament_name")
        or match_info.get("tournament_name")
        or match_info.get("league_slug")
    )
    if not _is_tournament_allowed(tournament):
        reasons["low_division"] += 1
        continue

print(f"\n📊 Статистика отсева (из {reasons['total']} проверенных):")
print(f"   ❌ Нет статистики: {reasons['no_stats']}")
print(f"   ⚖️  Ничейный счет: {reasons['draw_score']}")
print(f"   📉 Неполные метрики: {reasons['missing_metrics']}")
print(f"   ⏰ Слишком рано (<23 мин): {reasons['too_early']}")
print(f"   🏆 Низкая лига: {reasons['low_division']}")

