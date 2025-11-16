#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches
from graphql_live_analyzer import analyze_live_matches
from graphql_tennis_analyzer import analyze_live_tennis_matches
from generate_live_report import (
    MIN_ODDS, PRIMARY_MAX_ODDS, EXTENDED_MAX_ODDS,
    EXTENDED_MIN_DOMINANCE, EXTENDED_MIN_XG_DIFF, EXTENDED_MIN_SOT_DIFF
)

print("=" * 70)
print("АНАЛИЗ: ЖЕСТКИЕ ФИЛЬТРЫ ИЛИ МАЛО МАТЧЕЙ?")
print("=" * 70)

print("\nТЕКУЩИЕ НАСТРОЙКИ ФИЛЬТРОВ:")
print("-" * 70)
print(f"MIN_ODDS = {MIN_ODDS}")
print(f"PRIMARY_MAX_ODDS = {PRIMARY_MAX_ODDS} (кэфы 1.01-1.10)")
print(f"EXTENDED_MAX_ODDS = {EXTENDED_MAX_ODDS} (кэфы 1.11-1.50)")
print(f"EXTENDED_MIN_DOMINANCE = {EXTENDED_MIN_DOMINANCE}")
print(f"EXTENDED_MIN_XG_DIFF = {EXTENDED_MIN_XG_DIFF}")
print(f"EXTENDED_MIN_SOT_DIFF = {EXTENDED_MIN_SOT_DIFF}")

print("\n" + "=" * 70)
print("ШАГ 1: ПРОВЕРЯЮ ВСЕ LIVE МАТЧИ НА SCORES24")
print("-" * 70)

try:
    all_matches = fetch_live_matches()
    print(f"Всего live матчей на Scores24: {len(all_matches)}")
    
    if len(all_matches) == 0:
        print("\n[ВЫВОД] На Scores24 вообще нет live матчей прямо сейчас")
        print("Это не проблема фильтров - просто нет матчей")
        exit(0)
    
    # Разделяем по видам спорта
    football_matches = [m for m in all_matches if m.get("sport") == "soccer"]
    tennis_matches = [m for m in all_matches if m.get("sport") == "tennis"]
    
    print(f"  Футбол: {len(football_matches)}")
    print(f"  Теннис: {len(tennis_matches)}")
    print(f"  Другие: {len(all_matches) - len(football_matches) - len(tennis_matches)}")
    
except Exception as e:
    print(f"Ошибка при получении матчей: {e}")
    exit(1)

print("\n" + "=" * 70)
print("ШАГ 2: АНАЛИЗИРУЮ ФУТБОЛ (С ФИЛЬТРАМИ)")
print("-" * 70)

try:
    football_analyzed = analyze_live_matches()
    print(f"Футбольных матчей после анализа: {len(football_analyzed)}")
    
    if len(football_analyzed) == 0:
        print("\n[ПРОБЛЕМА] Футбольные матчи отфильтрованы на этапе анализа")
        print("Возможные причины:")
        print("  - Нет статистики (xG, удары, владение)")
        print("  - Молодежные/дружеские матчи")
        print("  - Низшие дивизионы")
        print("  - Отрицательный dominance (аутсайдер)")
    else:
        print(f"\nНайдено {len(football_analyzed)} матчей с положительным dominance")
        
except Exception as e:
    print(f"Ошибка при анализе футбола: {e}")

print("\n" + "=" * 70)
print("ШАГ 3: АНАЛИЗИРУЮ ТЕННИС (С ФИЛЬТРАМИ)")
print("-" * 70)

try:
    tennis_analyzed = analyze_live_tennis_matches()
    print(f"Теннисных матчей после анализа: {len(tennis_analyzed)}")
    
    if len(tennis_analyzed) == 0:
        print("\n[ПРОБЛЕМА] Теннисные матчи отфильтрованы на этапе анализа")
        print("Возможные причины:")
        print("  - Нет статистики (очки, брейки)")
        print("  - Неподходящие турниры")
        print("  - Отрицательный dominance")
    else:
        print(f"\nНайдено {len(tennis_analyzed)} матчей с положительным dominance")
        
except Exception as e:
    print(f"Ошибка при анализе тенниса: {e}")

print("\n" + "=" * 70)
print("ШАГ 4: ПРОВЕРЯЮ ФИЛЬТРЫ ПО КОЭФФИЦИЕНТАМ")
print("-" * 70)

# Собираем все проанализированные матчи
all_analyzed = []
try:
    all_analyzed.extend(analyze_live_matches())
except:
    pass
try:
    all_analyzed.extend(analyze_live_tennis_matches())
except:
    pass

if len(all_analyzed) == 0:
    print("\n[ВЫВОД] Нет матчей даже после базового анализа")
    print("Проблема НЕ в фильтрах по коэффициентам, а в:")
    print("  - Отсутствии статистики")
    print("  - Фильтрации молодежных/дружеских матчей")
    print("  - Отрицательном dominance")
else:
    print(f"\nМатчей после базового анализа: {len(all_analyzed)}")
    
    # Проверяем, сколько прошло бы фильтры
    from generate_live_report import _get_leader_odds, OddsInfo
    
    passed_primary = 0
    passed_extended = 0
    no_odds = 0
    too_low_odds = 0
    too_high_odds = 0
    failed_dominance = 0
    
    for match in all_analyzed[:20]:  # Проверяем первые 20
        sport = match.get("sport", "soccer")
        leader_index = match.get("leader_index", 0)
        slug = match.get("slug", "")
        
        # Получаем коэффициенты
        odds_info = _get_leader_odds(slug, leader_index, sport)
        
        if odds_info is None or odds_info.value is None:
            no_odds += 1
            continue
        
        odds = odds_info.value
        dominance = match.get("dominance_score", 0)
        minute_numeric = match.get("minute_numeric") or 0
        
        if odds < MIN_ODDS:
            too_low_odds += 1
            continue
        
        if odds <= PRIMARY_MAX_ODDS:
            # PRIMARY tier
            if minute_numeric < 30:
                required_dominance = 5.0
            else:
                required_dominance = 2.0
            
            xg_diff = abs(match.get("home_xg", 0) - match.get("away_xg", 0))
            sot_diff = abs(match.get("home_shots_on_target", 0) - match.get("away_shots_on_target", 0))
            
            if dominance >= required_dominance or (xg_diff >= 0.2 and sot_diff >= 1):
                passed_primary += 1
            else:
                failed_dominance += 1
        elif odds <= EXTENDED_MAX_ODDS:
            # EXTENDED tier
            if minute_numeric < 30:
                required_dominance = 8.0
            elif minute_numeric < 60:
                required_dominance = EXTENDED_MIN_DOMINANCE
            else:
                required_dominance = 5.0
            
            xg_diff = abs(match.get("home_xg", 0) - match.get("away_xg", 0))
            sot_diff = abs(match.get("home_shots_on_target", 0) - match.get("away_shots_on_target", 0))
            
            if (
                dominance >= required_dominance
                or (xg_diff >= EXTENDED_MIN_XG_DIFF and sot_diff >= EXTENDED_MIN_SOT_DIFF and minute_numeric >= 60)
            ):
                passed_extended += 1
            else:
                failed_dominance += 1
        else:
            too_high_odds += 1
    
    print(f"\nРезультаты проверки фильтров (первые 20 матчей):")
    print(f"  Прошло PRIMARY (1.01-1.10): {passed_primary}")
    print(f"  Прошло EXTENDED (1.11-1.50): {passed_extended}")
    print(f"  Нет коэффициентов: {no_odds}")
    print(f"  Коэффициент слишком низкий: {too_low_odds}")
    print(f"  Коэффициент слишком высокий (>1.50): {too_high_odds}")
    print(f"  Не прошло по dominance: {failed_dominance}")
    
    total_passed = passed_primary + passed_extended
    if total_passed == 0 and len(all_analyzed) > 0:
        print("\n[ВЫВОД] Фильтры ДЕЙСТВИТЕЛЬНО ЖЕСТКИЕ")
        print(f"Из {len(all_analyzed)} проанализированных матчей ни один не прошел фильтры")
    elif total_passed > 0:
        print(f"\n[ВЫВОД] Фильтры работают: {total_passed} матчей прошло")

print("\n" + "=" * 70)
print("ИТОГОВЫЙ ВЫВОД")
print("=" * 70)

if len(all_matches) == 0:
    print("На Scores24 нет live матчей - это не проблема фильтров")
elif len(football_analyzed) == 0 and len(tennis_analyzed) == 0:
    print("Матчи есть, но они отфильтрованы на этапе базового анализа")
    print("(нет статистики, молодежные/дружеские, отрицательный dominance)")
    print("Это НЕ проблема фильтров по коэффициентам")
else:
    print(f"Матчи после анализа: {len(all_analyzed)}")
    if len(all_analyzed) > 0 and total_passed == 0:
        print("Фильтры по коэффициентам ДЕЙСТВИТЕЛЬНО ЖЕСТКИЕ")
        print("Рекомендация: можно немного ослабить требования")

