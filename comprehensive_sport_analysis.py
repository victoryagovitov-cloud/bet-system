#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Комплексный анализ всех видов спорта"""

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_live_analyzer import analyze_live_matches, _parse_score, _parse_minute_value, MINIMUM_MINUTE_THRESHOLD
from graphql_tennis_analyzer import analyze_live_tennis_matches
from graphql_handball_analyzer import analyze_live_handball_matches, _parse_minute, _parse_int, _parse_score as _parse_handball_score
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 80)
print("КОМПЛЕКСНЫЙ АНАЛИЗ ВСЕХ ВИДОВ СПОРТА")
print("=" * 80)

# ========== ФУТБОЛ ==========
print("\n" + "=" * 80)
print("⚽ ФУТБОЛ")
print("=" * 80)

all_football = fetch_live_matches(limit=50, sport="soccer")
print(f"\n📊 Всего live матчей: {len(all_football)}")

football_stats = {
    "total": len(all_football),
    "no_stats": 0,
    "no_score": 0,
    "draw": 0,
    "no_minute": 0,
    "too_early": 0,
    "missing_metrics": 0,
    "passed": 0
}

for match_info in all_football[:30]:
    slug = match_info["slug"]
    try:
        details = fetch_match_stats(slug, sport="soccer")
    except:
        football_stats["no_stats"] += 1
        continue
    
    score = _parse_score(details)
    if not score:
        football_stats["no_score"] += 1
        continue
    
    if score[0] == score[1]:
        football_stats["draw"] += 1
        continue
    
    minute = _parse_minute_value(details.get("minute") or match_info.get("minute"))
    if minute is None:
        football_stats["no_minute"] += 1
        continue
    
    if minute < MINIMUM_MINUTE_THRESHOLD:
        football_stats["too_early"] += 1
        continue
    
    # Проверка метрик
    from graphql_live_analyzer import _extract_totals
    totals = _extract_totals(details.get("statistic"))
    possession = totals.get("ball_possession")
    shots_on_target = totals.get("shots_on_target") or totals.get("shots_on_goal")
    
    if not possession or possession[0] is None or possession[1] is None:
        football_stats["missing_metrics"] += 1
        continue
    
    if not shots_on_target or shots_on_target[0] is None or shots_on_target[1] is None:
        football_stats["missing_metrics"] += 1
        continue
    
    football_stats["passed"] += 1

print(f"✅ Прошли фильтры: {football_stats['passed']}")
print(f"❌ Отсеяно:")
print(f"   Нет статистики: {football_stats['no_stats']}")
print(f"   Нет счета: {football_stats['no_score']}")
print(f"   Ничейный: {football_stats['draw']}")
print(f"   Нет минуты: {football_stats['no_minute']}")
print(f"   Слишком рано (<{MINIMUM_MINUTE_THRESHOLD} мин): {football_stats['too_early']}")
print(f"   Неполные метрики: {football_stats['missing_metrics']}")

# ========== ТЕННИС ==========
print("\n" + "=" * 80)
print("🎾 ТЕННИС")
print("=" * 80)

all_tennis = fetch_live_matches(limit=50, sport="tennis")
print(f"\n📊 Всего live матчей: {len(all_tennis)}")

tennis_stats = {
    "total": len(all_tennis),
    "no_stats": 0,
    "no_score": 0,
    "no_sets": 0,
    "passed": 0
}

for match_info in all_tennis[:30]:
    slug = match_info["slug"]
    try:
        details = fetch_match_stats(slug, sport="tennis")
    except:
        tennis_stats["no_stats"] += 1
        continue
    
    # Проверяем счет сетов
    result_scores = details.get("result_scores") or []
    if not result_scores:
        tennis_stats["no_score"] += 1
        continue
    
    # Проверяем, есть ли хотя бы один завершенный сет
    sets_finished = [s for s in result_scores if s.get("type") == "set" and s.get("value")]
    if not sets_finished:
        tennis_stats["no_sets"] += 1
        continue
    
    tennis_stats["passed"] += 1

print(f"✅ Прошли базовые фильтры: {tennis_stats['passed']}")
print(f"❌ Отсеяно:")
print(f"   Нет статистики: {tennis_stats['no_stats']}")
print(f"   Нет счета: {tennis_stats['no_score']}")
print(f"   Нет завершенных сетов: {tennis_stats['no_sets']}")

# Проверяем через анализатор
try:
    analyzed_tennis = analyze_live_tennis_matches(limit=30)
    print(f"\n📈 Через анализатор: {len(analyzed_tennis)} матчей")
except Exception as e:
    print(f"\n❌ Ошибка анализатора тенниса: {e}")

# ========== ГАНДБОЛ ==========
print("\n" + "=" * 80)
print("🤾 ГАНДБОЛ")
print("=" * 80)

all_handball = fetch_live_matches(limit=50, sport="handball")
print(f"\n📊 Всего live матчей: {len(all_handball)}")

handball_stats = {
    "total": len(all_handball),
    "no_stats": 0,
    "no_score": 0,
    "no_minute": 0,
    "too_early": 0,
    "too_late": 0,
    "low_total": 0,
    "draw": 0,
    "low_diff": 0,
    "passed": 0
}

for match_info in all_handball[:30]:
    slug = match_info["slug"]
    try:
        details = fetch_match_stats(slug, sport="handball")
    except:
        handball_stats["no_stats"] += 1
        continue
    
    # Парсинг счета
    game_state = details.get("game_state") or {}
    home_score = _parse_int(game_state.get("home_score"))
    away_score = _parse_int(game_state.get("away_score"))
    
    if home_score is None or away_score is None:
        parsed = _parse_handball_score(details.get("result_score"))
        if not parsed:
            handball_stats["no_score"] += 1
            continue
        home_score, away_score = parsed
    
    # Парсинг минуты
    minute = _parse_minute(details.get("minute") or match_info.get("minute"))
    if minute is None:
        handball_stats["no_minute"] += 1
        continue
    
    if minute < 32:
        handball_stats["too_early"] += 1
        continue
    
    if minute >= 60:
        handball_stats["too_late"] += 1
        continue
    
    total_score = home_score + away_score
    if total_score < 25:
        handball_stats["low_total"] += 1
        continue
    
    if home_score == away_score:
        handball_stats["draw"] += 1
        continue
    
    score_diff = abs(home_score - away_score)
    diff_threshold = 3 if minute >= 45 else 4
    if score_diff < diff_threshold:
        handball_stats["low_diff"] += 1
        continue
    
    handball_stats["passed"] += 1

print(f"✅ Прошли фильтры: {handball_stats['passed']}")
print(f"❌ Отсеяно:")
print(f"   Нет статистики: {handball_stats['no_stats']}")
print(f"   Нет счета: {handball_stats['no_score']}")
print(f"   Нет минуты: {handball_stats['no_minute']}")
print(f"   Слишком рано (<32 мин): {handball_stats['too_early']}")
print(f"   Слишком поздно (≥60 мин): {handball_stats['too_late']}")
print(f"   Низкий тотал (<25): {handball_stats['low_total']}")
print(f"   Ничейный: {handball_stats['draw']}")
print(f"   Малая разница: {handball_stats['low_diff']}")

# Проверяем через анализатор
try:
    analyzed_handball = analyze_live_handball_matches(limit=30)
    print(f"\n📈 Через анализатор: {len(analyzed_handball)} матчей")
except Exception as e:
    print(f"\n❌ Ошибка анализатора гандбола: {e}")

# ========== ИТОГОВЫЙ АНАЛИЗ ==========
print("\n" + "=" * 80)
print("🔍 ИТОГОВЫЙ АНАЛИЗ ПРОБЛЕМ")
print("=" * 80)

print("\n📊 СВОДКА:")
print(f"   Футбол: {football_stats['passed']} из {football_stats['total']} ({football_stats['passed']/max(football_stats['total'],1)*100:.1f}%)")
print(f"   Теннис: {tennis_stats['passed']} из {tennis_stats['total']} ({tennis_stats['passed']/max(tennis_stats['total'],1)*100:.1f}%)")
print(f"   Гандбол: {handball_stats['passed']} из {handball_stats['total']} ({handball_stats['passed']/max(handball_stats['total'],1)*100:.1f}%)")

print("\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")

# Проблема 1: Гандбол - нет минуты
if handball_stats['no_minute'] > 0:
    print(f"\n1. ГАНДБОЛ: {handball_stats['no_minute']} матчей без минуты")
    print("   → Проблема: minute = None в данных")
    print("   → Решение: использовать альтернативные источники или снизить требование к минуте")

# Проблема 2: Футбол - нет минуты
if football_stats['no_minute'] > 0:
    print(f"\n2. ФУТБОЛ: {football_stats['no_minute']} матчей без минуты")
    print("   → Проблема: minute = None в данных")
    print("   → Решение: использовать альтернативные источники или сделать минуту опциональной для некоторых матчей")

# Проблема 3: Гандбол - слишком строгие критерии
if handball_stats['low_diff'] > 0 and handball_stats['passed'] == 0:
    print(f"\n3. ГАНДБОЛ: {handball_stats['low_diff']} матчей отсеяно из-за малой разницы")
    print("   → Проблема: требование разницы ≥3-4 гола слишком строгое")
    print("   → Решение: снизить порог до 2-3 голов")

# Проблема 4: Гандбол - слишком рано
if handball_stats['too_early'] > 0:
    print(f"\n4. ГАНДБОЛ: {handball_stats['too_early']} матчей отсеяно (слишком рано <32 мин)")
    print("   → Проблема: требование ≥32 минуты слишком строгое")
    print("   → Решение: снизить порог до 25-28 минут")

print("\n💡 РЕКОМЕНДАЦИИ:")
total_passed = football_stats['passed'] + tennis_stats['passed'] + handball_stats['passed']
if total_passed < 8:
    print(f"   Нужно минимум 8 матчей в день, сейчас: {total_passed}")
    print("   Приоритет исправлений:")
    print("   1. Гандбол: исправить парсинг минуты или сделать опциональным")
    print("   2. Гандбол: снизить пороги (минута до 25, разница до 2-3)")
    print("   3. Футбол: проверить парсинг минуты для матчей без minute")

