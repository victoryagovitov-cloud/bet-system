#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Глубокий анализ: почему так мало матчей проходит"""

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_live_analyzer import _parse_score, _extract_totals, _parse_minute_value, _is_tournament_allowed, MINIMUM_MINUTE_THRESHOLD
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 60)
print("ГЛУБОКИЙ АНАЛИЗ ФИЛЬТРАЦИИ")
print("=" * 60)

# Шаг 1: Сколько всего live матчей
all_live = fetch_live_matches(limit=100)
print(f"\n1️⃣ Всего live матчей: {len(all_live)}")

# Шаг 2: Анализ каждого этапа фильтрации
stats = {
    "total": len(all_live),
    "no_stats": 0,
    "no_score": 0,
    "draw_score": 0,
    "missing_possession": 0,
    "missing_shots_total": 0,
    "missing_shots_on_target": 0,
    "too_early": 0,
    "low_division": 0,
    "passed": 0
}

examples = {
    "no_stats": [],
    "no_score": [],
    "draw_score": [],
    "missing_possession": [],
    "missing_shots_total": [],
    "missing_shots_on_target": [],
    "too_early": [],
    "low_division": [],
    "passed": []
}

for match_info in all_live:
    slug = match_info["slug"]
    teams = match_info.get("teams", [])
    home = teams[0].get("name", "?") if teams else "?"
    away = teams[1].get("name", "?") if len(teams) > 1 else "?"
    
    # Этап 1: Получение статистики
    try:
        details = fetch_match_stats(slug)
    except Exception as e:
        stats["no_stats"] += 1
        if len(examples["no_stats"]) < 3:
            examples["no_stats"].append(f"{home} vs {away}")
        continue
    
    # Этап 2: Парсинг счета
    score = _parse_score(details)
    if not score:
        stats["no_score"] += 1
        if len(examples["no_score"]) < 3:
            examples["no_score"].append(f"{home} vs {away}")
        continue
    
    home_score, away_score = score
    if home_score == away_score:
        stats["draw_score"] += 1
        if len(examples["draw_score"]) < 3:
            examples["draw_score"].append(f"{home} vs {away} - {home_score}:{away_score}")
        continue
    
    # Этап 3: Проверка метрик
    totals = _extract_totals(details.get("statistic"))
    possession = totals.get("ball_possession")
    shots_total = totals.get("shots_total")
    shots_on_target = totals.get("shots_on_target") or totals.get("shots_on_goal")
    
    if not possession or possession[0] is None or possession[1] is None:
        stats["missing_possession"] += 1
        if len(examples["missing_possession"]) < 3:
            examples["missing_possession"].append(f"{home} vs {away} - {home_score}:{away_score}")
        continue
    
    if not shots_total or shots_total[0] is None or shots_total[1] is None:
        stats["missing_shots_total"] += 1
        if len(examples["missing_shots_total"]) < 3:
            examples["missing_shots_total"].append(f"{home} vs {away} - {home_score}:{away_score}")
        continue
    
    if not shots_on_target or shots_on_target[0] is None or shots_on_target[1] is None:
        stats["missing_shots_on_target"] += 1
        if len(examples["missing_shots_on_target"]) < 3:
            examples["missing_shots_on_target"].append(f"{home} vs {away} - {home_score}:{away_score}")
        continue
    
    # Этап 4: Проверка минуты
    minute_numeric = _parse_minute_value(details.get("minute"))
    if minute_numeric is None:
        minute_numeric = _parse_minute_value(match_info.get("minute"))
    if minute_numeric is not None and minute_numeric < MINIMUM_MINUTE_THRESHOLD:
        stats["too_early"] += 1
        if len(examples["too_early"]) < 3:
            examples["too_early"].append(f"{home} vs {away} - {home_score}:{away_score} ({minute_numeric}')")
        continue
    
    # Этап 5: Проверка турнира
    tournament = (
        (details.get("unique_tournament") or {}).get("name")
        or details.get("tournament_name")
        or match_info.get("tournament_name")
        or match_info.get("league_slug")
    )
    if not _is_tournament_allowed(tournament):
        stats["low_division"] += 1
        if len(examples["low_division"]) < 3:
            examples["low_division"].append(f"{home} vs {away} - {tournament}")
        continue
    
    # Прошел все фильтры!
    stats["passed"] += 1
    if len(examples["passed"]) < 5:
        examples["passed"].append({
            "teams": f"{home} vs {away}",
            "score": f"{home_score}:{away_score}",
            "minute": minute_numeric,
            "tournament": tournament
        })

print("\n" + "=" * 60)
print("ДЕТАЛЬНАЯ СТАТИСТИКА ОТСЕВА:")
print("=" * 60)
print(f"Всего проверено: {stats['total']}")
print(f"✅ Прошли все фильтры: {stats['passed']}")
print(f"\n❌ Отсеяно:")
print(f"   Нет статистики: {stats['no_stats']}")
print(f"   Нет счета: {stats['no_score']}")
print(f"   Ничейный счет: {stats['draw_score']}")
print(f"   Нет владения: {stats['missing_possession']}")
print(f"   Нет ударов всего: {stats['missing_shots_total']}")
print(f"   Нет ударов в створ: {stats['missing_shots_on_target']}")
print(f"   Слишком рано (<{MINIMUM_MINUTE_THRESHOLD} мин): {stats['too_early']}")
print(f"   Низкая лига: {stats['low_division']}")

print("\n" + "=" * 60)
print("ПРИМЕРЫ ПРОШЕДШИХ:")
print("=" * 60)
for ex in examples["passed"]:
    print(f"  {ex['teams']} - {ex['score']} ({ex['minute']}') | {ex['tournament']}")

if examples["missing_shots_total"]:
    print("\n" + "=" * 60)
    print("ПРИМЕРЫ: НЕТ УДАРОВ ВСЕГО (можно сделать опциональным?)")
    print("=" * 60)
    for ex in examples["missing_shots_total"][:5]:
        print(f"  {ex}")

if examples["missing_shots_on_target"]:
    print("\n" + "=" * 60)
    print("ПРИМЕРЫ: НЕТ УДАРОВ В СТВОР (можно сделать опциональным?)")
    print("=" * 60)
    for ex in examples["missing_shots_on_target"][:5]:
        print(f"  {ex}")

print("\n" + "=" * 60)
print("РЕКОМЕНДАЦИИ:")
print("=" * 60)

if stats["missing_shots_total"] > 0:
    print(f"1. shots_total отсутствует у {stats['missing_shots_total']} матчей")
    print("   → СДЕЛАТЬ ОПЦИОНАЛЬНЫМ (использовать только shots_on_target)")
    
if stats["missing_shots_on_target"] > 0:
    print(f"2. shots_on_target отсутствует у {stats['missing_shots_on_target']} матчей")
    print("   → Оставить обязательным (это ключевая метрика)")

if stats["too_early"] > 0:
    print(f"3. Слишком рано (<{MINIMUM_MINUTE_THRESHOLD} мин): {stats['too_early']} матчей")
    print(f"   → Снизить порог до 15-18 минут?")

if stats["passed"] < 8:
    missing = 8 - stats["passed"]
    print(f"\n4. Нужно еще {missing} матчей для минимума (8 в день)")
    print("   → Комбинация:")
    print("     - shots_total опциональный")
    print("     - Снизить порог минуты до 15")
    print("     - Это даст примерно +{stats['missing_shots_total'] + stats['too_early']} матчей")

