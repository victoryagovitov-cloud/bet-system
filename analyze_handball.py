#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Анализ гандбольных матчей"""

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_handball_analyzer import analyze_live_handball_matches, _parse_minute, _parse_int, _parse_score, _is_allowed_handball_tournament
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 60)
print("АНАЛИЗ ГАНДБОЛЬНЫХ МАТЧЕЙ")
print("=" * 60)

# Шаг 1: Сколько всего live гандбольных матчей
all_handball = fetch_live_matches(limit=100, sport="handball")
print(f"\n1️⃣ Всего live гандбольных матчей: {len(all_handball)}")

# Шаг 2: Анализ фильтрации
stats = {
    "total": len(all_handball),
    "no_stats": 0,
    "tournament_disallowed": 0,
    "too_early": 0,
    "too_late": 0,
    "no_score": 0,
    "low_total": 0,
    "draw_score": 0,
    "low_diff": 0,
    "no_statistic": 0,
    "passed": 0
}

examples = {
    "tournament_disallowed": [],
    "too_early": [],
    "too_late": [],
    "no_score": [],
    "low_total": [],
    "draw_score": [],
    "low_diff": [],
    "no_statistic": [],
    "passed": []
}

for match_info in all_handball:
    slug = match_info["slug"]
    teams = match_info.get("teams", [])
    home = teams[0].get("name", "?") if teams else "?"
    away = teams[1].get("name", "?") if len(teams) > 1 else "?"
    
    # Этап 1: Получение статистики
    try:
        details = fetch_match_stats(slug, sport="handball")
    except Exception as e:
        stats["no_stats"] += 1
        continue
    
    # Этап 2: Проверка турнира
    tournament_name = (
        (details.get("unique_tournament") or {}).get("name")
        or details.get("tournament_name")
        or match_info.get("tournament_name")
        or match_info.get("category_name")
        or match_info.get("league_slug")
        or ""
    )
    if not _is_allowed_handball_tournament(tournament_name):
        stats["tournament_disallowed"] += 1
        if len(examples["tournament_disallowed"]) < 5:
            examples["tournament_disallowed"].append(f"{home} vs {away} - {tournament_name}")
        continue
    
    # Этап 3: Проверка минуты
    minute_numeric = _parse_minute(details.get("minute") or match_info.get("minute"))
    if minute_numeric is None:
        stats["no_score"] += 1
        if len(examples["no_score"]) < 3:
            examples["no_score"].append(f"{home} vs {away}")
        continue
    
    if minute_numeric < 32:
        stats["too_early"] += 1
        if len(examples["too_early"]) < 5:
            examples["too_early"].append(f"{home} vs {away} - {minute_numeric}'")
        continue
    
    if minute_numeric >= 60:
        stats["too_late"] += 1
        if len(examples["too_late"]) < 3:
            examples["too_late"].append(f"{home} vs {away} - {minute_numeric}'")
        continue
    
    # Этап 4: Проверка счета
    game_state = details.get("game_state") or {}
    home_score = _parse_int(game_state.get("home_score"))
    away_score = _parse_int(game_state.get("away_score"))
    if home_score is None or away_score is None:
        parsed = _parse_score(details.get("result_score"))
        if not parsed:
            stats["no_score"] += 1
            continue
        home_score, away_score = parsed
    
    total_score = home_score + away_score
    if total_score < 25:
        stats["low_total"] += 1
        if len(examples["low_total"]) < 3:
            examples["low_total"].append(f"{home} vs {away} - {home_score}:{away_score} (всего {total_score})")
        continue
    
    if home_score == away_score:
        stats["draw_score"] += 1
        if len(examples["draw_score"]) < 3:
            examples["draw_score"].append(f"{home} vs {away} - {home_score}:{away_score}")
        continue
    
    # Этап 5: Проверка разницы
    score_diff = abs(home_score - away_score)
    diff_threshold = 3 if minute_numeric >= 45 else 4
    if score_diff < diff_threshold:
        stats["low_diff"] += 1
        if len(examples["low_diff"]) < 5:
            examples["low_diff"].append(f"{home} vs {away} - {home_score}:{away_score} (разница {score_diff}, нужно ≥{diff_threshold})")
        continue
    
    # Этап 6: Проверка статистики
    if details.get("statistic") and not details["statistic"].get("periods"):
        stats["no_statistic"] += 1
        if len(examples["no_statistic"]) < 3:
            examples["no_statistic"].append(f"{home} vs {away}")
        continue
    
    # Прошел все фильтры!
    stats["passed"] += 1
    if len(examples["passed"]) < 10:
        examples["passed"].append({
            "teams": f"{home} vs {away}",
            "score": f"{home_score}:{away_score}",
            "minute": minute_numeric,
            "diff": score_diff,
            "total": total_score,
            "tournament": tournament_name
        })

print("\n" + "=" * 60)
print("ДЕТАЛЬНАЯ СТАТИСТИКА ОТСЕВА:")
print("=" * 60)
print(f"Всего проверено: {stats['total']}")
print(f"✅ Прошли все фильтры: {stats['passed']}")
print(f"\n❌ Отсеяно:")
print(f"   Нет статистики: {stats['no_stats']}")
print(f"   Турнир не разрешен: {stats['tournament_disallowed']}")
print(f"   Слишком рано (<32 мин): {stats['too_early']}")
print(f"   Слишком поздно (≥60 мин): {stats['too_late']}")
print(f"   Нет счета: {stats['no_score']}")
print(f"   Низкий тотал (<25): {stats['low_total']}")
print(f"   Ничейный счет: {stats['draw_score']}")
print(f"   Малая разница: {stats['low_diff']}")
print(f"   Нет статистики в деталях: {stats['no_statistic']}")

print("\n" + "=" * 60)
print("ПРИМЕРЫ ПРОШЕДШИХ:")
print("=" * 60)
for ex in examples["passed"][:10]:
    print(f"  {ex['teams']} - {ex['score']} ({ex['minute']}') | разница {ex['diff']} | тотал {ex['total']} | {ex['tournament']}")

if examples["too_early"]:
    print("\n" + "=" * 60)
    print("ПРИМЕРЫ: СЛИШКОМ РАНО (<32 мин) - можно снизить порог?")
    print("=" * 60)
    for ex in examples["too_early"][:5]:
        print(f"  {ex}")

if examples["low_diff"]:
    print("\n" + "=" * 60)
    print("ПРИМЕРЫ: МАЛАЯ РАЗНИЦА - можно снизить порог?")
    print("=" * 60)
    for ex in examples["low_diff"][:5]:
        print(f"  {ex}")

if examples["tournament_disallowed"]:
    print("\n" + "=" * 60)
    print("ПРИМЕРЫ: ТУРНИР НЕ РАЗРЕШЕН - может быть стоит разрешить?")
    print("=" * 60)
    for ex in examples["tournament_disallowed"][:5]:
        print(f"  {ex}")

print("\n" + "=" * 60)
print("РЕКОМЕНДАЦИИ:")
print("=" * 60)

if stats["too_early"] > 0:
    print(f"1. Слишком рано (<32 мин): {stats['too_early']} матчей")
    print("   → СНИЗИТЬ ПОРОГ ДО 25-28 МИНУТ")

if stats["low_diff"] > 0:
    print(f"2. Малая разница: {stats['low_diff']} матчей")
    print("   → СНИЗИТЬ ПОРОГ: 3 гола (если >=40 мин) или 2 гола (если >=45 мин)")

if stats["tournament_disallowed"] > 0:
    print(f"3. Турнир не разрешен: {stats['tournament_disallowed']} матчей")
    print("   → Проверить список DISALLOWED - может быть слишком строгий?")

if stats["passed"] < 3:
    missing = 3 - stats["passed"]
    print(f"\n4. Нужно еще {missing} матчей для минимума")
    print("   → Комбинация:")
    if stats["too_early"] > 0:
        print(f"     - Снизить порог минуты до 25-28 (+{min(stats['too_early'], 5)} матчей)")
    if stats["low_diff"] > 0:
        print(f"     - Снизить порог разницы (+{min(stats['low_diff'], 5)} матчей)")

