#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Полная проверка системы по всем видам спорта"""

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_live_analyzer import analyze_live_matches
from graphql_tennis_analyzer import analyze_live_tennis_matches
from graphql_handball_analyzer import analyze_live_handball_matches, _parse_minute, _parse_int, _parse_score
from generate_live_report import _get_leader_odds, PRIMARY_MAX_ODDS, EXTENDED_MAX_ODDS
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 80)
print("ПОЛНАЯ ПРОВЕРКА СИСТЕМЫ: ФУТБОЛ, ТЕННИС, ГАНДБОЛ")
print("=" * 80)

# ========== ФУТБОЛ ==========
print("\n" + "=" * 80)
print("⚽ ФУТБОЛ")
print("=" * 80)

all_football = fetch_live_matches(limit=100, sport="soccer")
print(f"Всего live матчей: {len(all_football)}")

analyzed_football = analyze_live_matches(limit=100)
print(f"Прошли базовую фильтрацию: {len(analyzed_football)}")

# Проверяем с коэффициентами
football_with_odds = []
for match in analyzed_football:
    if match.get("dominance_score", 0) <= 0:
        continue
    odds = _get_leader_odds(match["slug"], match["leader_index"])
    if odds.value is None:
        continue
    if odds.value <= PRIMARY_MAX_ODDS:
        football_with_odds.append(match)
    elif odds.value <= EXTENDED_MAX_ODDS and match.get("dominance_score", 0) >= 10.0:
        football_with_odds.append(match)

print(f"Прошли фильтр по кэфу: {len(football_with_odds)}")

if football_with_odds:
    print("\nПримеры:")
    for m in football_with_odds[:3]:
        odds = _get_leader_odds(m["slug"], m["leader_index"])
        print(f"  {m['teams'][0]} vs {m['teams'][1]} - {m['score']} ({m['minute']}') | кэф {odds.value:.2f}")

# ========== ТЕННИС ==========
print("\n" + "=" * 80)
print("🎾 ТЕННИС")
print("=" * 80)

all_tennis = fetch_live_matches(limit=100, sport="tennis")
print(f"Всего live матчей: {len(all_tennis)}")

analyzed_tennis = analyze_live_tennis_matches(limit=100)
print(f"Прошли базовую фильтрацию: {len(analyzed_tennis)}")

# Проверяем с коэффициентами
tennis_with_odds = []
for match in analyzed_tennis:
    if match.get("dominance_score", 0) <= 0:
        continue
    odds = _get_leader_odds(match["slug"], match["leader_index"], sport="tennis")
    if odds.value is None:
        continue
    if odds.value <= PRIMARY_MAX_ODDS:
        tennis_with_odds.append(match)
    elif odds.value <= EXTENDED_MAX_ODDS and match.get("dominance_score", 0) >= 10.0:
        tennis_with_odds.append(match)

print(f"Прошли фильтр по кэфу: {len(tennis_with_odds)}")

if tennis_with_odds:
    print("\nПримеры:")
    for m in tennis_with_odds[:3]:
        odds = _get_leader_odds(m["slug"], m["leader_index"], sport="tennis")
        print(f"  {m['teams'][0]} vs {m['teams'][1]} - {m.get('sets_score', '?')} | кэф {odds.value:.2f}")

# ========== ГАНДБОЛ ==========
print("\n" + "=" * 80)
print("🤾 ГАНДБОЛ")
print("=" * 80)

all_handball = fetch_live_matches(limit=100, sport="handball")
print(f"Всего live матчей: {len(all_handball)}")

# Детальная проверка гандбола
handball_stats = {
    "total": len(all_handball),
    "no_stats": 0,
    "no_score": 0,
    "no_minute": 0,
    "too_early": 0,
    "draw": 0,
    "low_total": 0,
    "low_diff": 0,
    "passed_basic": 0
}

for match_info in all_handball[:30]:  # Проверяем первые 30
    slug = match_info["slug"]
    teams = match_info.get("teams", [])
    home = teams[0].get("name", "?") if teams else "?"
    away = teams[1].get("name", "?") if len(teams) > 1 else "?"
    
    try:
        details = fetch_match_stats(slug, sport="handball")
    except Exception:
        handball_stats["no_stats"] += 1
        continue
    
    # Проверка счета
    game_state = details.get("game_state") or {}
    home_score = _parse_int(game_state.get("home_score"))
    away_score = _parse_int(game_state.get("away_score"))
    if home_score is None or away_score is None:
        parsed = _parse_score(details.get("result_score"))
        if not parsed:
            handball_stats["no_score"] += 1
            continue
        home_score, away_score = parsed
    
    # Проверка минуты
    minute_numeric = _parse_minute(details.get("minute") or match_info.get("minute"))
    if minute_numeric is None:
        handball_stats["no_minute"] += 1
        continue
    
    if minute_numeric < 32:
        handball_stats["too_early"] += 1
        continue
    
    if home_score == away_score:
        handball_stats["draw"] += 1
        continue
    
    total_score = home_score + away_score
    if total_score < 25:
        handball_stats["low_total"] += 1
        continue
    
    score_diff = abs(home_score - away_score)
    diff_threshold = 3 if minute_numeric >= 45 else 4
    if score_diff < diff_threshold:
        handball_stats["low_diff"] += 1
        continue
    
    handball_stats["passed_basic"] += 1

print(f"Детальная статистика (первые 30):")
print(f"  Нет статистики: {handball_stats['no_stats']}")
print(f"  Нет счета: {handball_stats['no_score']}")
print(f"  Нет минуты: {handball_stats['no_minute']} ⚠️ ПРОБЛЕМА!")
print(f"  Слишком рано (<32 мин): {handball_stats['too_early']}")
print(f"  Ничейный: {handball_stats['draw']}")
print(f"  Низкий тотал (<25): {handball_stats['low_total']}")
print(f"  Малая разница: {handball_stats['low_diff']}")
print(f"  Прошли базовую фильтрацию: {handball_stats['passed_basic']}")

analyzed_handball = analyze_live_handball_matches(limit=100)
print(f"\nЧерез analyze_live_handball_matches: {len(analyzed_handball)}")

# Проверяем с коэффициентами
handball_with_odds = []
for match in analyzed_handball:
    if match.get("dominance_score", 0) <= 0:
        continue
    odds = _get_leader_odds(match["slug"], match["leader_index"], sport="handball")
    if odds.value is None:
        continue
    if odds.value <= PRIMARY_MAX_ODDS:
        handball_with_odds.append(match)
    elif odds.value <= EXTENDED_MAX_ODDS and match.get("dominance_score", 0) >= 10.0:
        handball_with_odds.append(match)

print(f"Прошли фильтр по кэфу: {len(handball_with_odds)}")

if handball_with_odds:
    print("\nПримеры:")
    for m in handball_with_odds[:3]:
        odds = _get_leader_odds(m["slug"], m["leader_index"], sport="handball")
        print(f"  {m['teams'][0]} vs {m['teams'][1]} - {m['score']} ({m['minute']}') | кэф {odds.value:.2f}")

# ========== ИТОГИ ==========
print("\n" + "=" * 80)
print("📊 ИТОГИ")
print("=" * 80)

total_passed = len(football_with_odds) + len(tennis_with_odds) + len(handball_with_odds)
print(f"\nВсего матчей прошло все фильтры: {total_passed}")
print(f"  Футбол: {len(football_with_odds)}")
print(f"  Теннис: {len(tennis_with_odds)}")
print(f"  Гандбол: {len(handball_with_odds)}")

print("\n" + "=" * 80)
print("🔍 НАЙДЕННЫЕ ПРОБЛЕМЫ:")
print("=" * 80)

if handball_stats["no_minute"] > 0:
    print(f"\n❌ ГАНДБОЛ: {handball_stats['no_minute']} матчей без минуты")
    print("   → Проблема: minute = None в данных")
    print("   → Решение: использовать альтернативные источники или снизить требование к минуте")

if len(analyzed_football) > 0 and len(football_with_odds) == 0:
    print(f"\n⚠️  ФУТБОЛ: {len(analyzed_football)} матчей прошли фильтры, но 0 прошли по кэфу")
    print("   → Проблема: все кэфы > 1.85 или нет коэффициентов")
    print("   → Решение: проверить получение коэффициентов")

if len(analyzed_tennis) > 0 and len(tennis_with_odds) == 0:
    print(f"\n⚠️  ТЕННИС: {len(analyzed_tennis)} матчей прошли фильтры, но 0 прошли по кэфу")
    print("   → Проблема: все кэфы > 1.85 или нет коэффициентов")

if total_passed < 8:
    print(f"\n❌ КРИТИЧНО: Всего {total_passed} матчей, нужно минимум 8")
    print("   → Нужно ослабить критерии или увеличить лимит кэф")

