#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_match_stats
from graphql_live_analyzer import _parse_score, _extract_totals

print("=" * 60)
print("ПРОВЕРКА МАТЧЕЙ С ОТРИЦАТЕЛЬНЫМ ДОМИНИРОВАНИЕМ")
print("=" * 60)

# Матчи из предыдущего анализа
matches_to_check = [
    ("12-11-2025-brighton-w-charlton-athletic-w-", "Брайтон (Ж)", "Чарльтон Атлетик (Ж)", 0, 1),
    ("12-11-2025-juventude-brasil-de-pelotas", "Жувентуде", "Бразил де Пелотас", 0, 1),
]

for slug, home_name, away_name, home_score, away_score in matches_to_check:
    print(f"\n{home_name} - {away_name}")
    print(f"Счет: {home_score}:{away_score}")
    print(f"Slug: {slug}")
    
    try:
        details = fetch_match_stats(slug)
    except Exception as e:
        print(f"Ошибка получения статистики: {e}")
        continue
    
    # Проверяем счет еще раз
    score = _parse_score(details)
    if score:
        print(f"Счет из API: {score[0]}:{score[1]}")
    
    # Получаем статистику
    totals = _extract_totals(details.get("statistic"))
    xg = totals.get("xg")
    possession = totals.get("ball_possession")
    shots_on_target = totals.get("shots_on_target") or totals.get("shots_on_goal")
    shots_total = totals.get("shots_total")
    
    print(f"\nСтатистика:")
    print(f"  xG: {xg}")
    print(f"  Владение: {possession}")
    print(f"  Удары в створ: {shots_on_target}")
    print(f"  Всего ударов: {shots_total}")
    
    # Лидер по счету - гости (индекс 1)
    leader_index = 1
    trailing_index = 0
    
    if possession:
        leader_poss = possession[leader_index] if possession else None
        trailing_poss = possession[trailing_index] if possession else None
        print(f"\n  Владение лидера (гости): {leader_poss}%")
        print(f"  Владение проигрывающего (домашние): {trailing_poss}%")
        if leader_poss and trailing_poss:
            print(f"  Разница: {leader_poss - trailing_poss}%")
    
    if shots_on_target:
        leader_sot = shots_on_target[leader_index] if shots_on_target else None
        trailing_sot = shots_on_target[trailing_index] if shots_on_target else None
        print(f"\n  Удары в створ лидера (гости): {leader_sot}")
        print(f"  Удары в створ проигрывающего (домашние): {trailing_sot}")
        if leader_sot is not None and trailing_sot is not None:
            print(f"  Разница: {leader_sot - trailing_sot}")
    
    if xg:
        leader_xg = xg[leader_index] if xg else None
        trailing_xg = xg[trailing_index] if xg else None
        print(f"\n  xG лидера (гости): {leader_xg}")
        print(f"  xG проигрывающего (домашние): {trailing_xg}")
        if leader_xg is not None and trailing_xg is not None:
            print(f"  Разница: {leader_xg - trailing_xg}")
    
    # Вычисляем доминирование вручную
    import math
    leader_metrics = {
        "xg": xg[leader_index] if xg and xg[leader_index] is not None else math.nan,
        "possession": possession[leader_index] if possession and possession[leader_index] is not None else math.nan,
        "shots_total": shots_total[leader_index] if shots_total and shots_total[leader_index] is not None else math.nan,
        "shots_on_target": shots_on_target[leader_index] if shots_on_target and shots_on_target[leader_index] is not None else math.nan,
    }
    trailing_metrics = {
        "xg": xg[trailing_index] if xg and xg[trailing_index] is not None else math.nan,
        "possession": possession[trailing_index] if possession and possession[trailing_index] is not None else math.nan,
        "shots_total": shots_total[trailing_index] if shots_total and shots_total[trailing_index] is not None else math.nan,
        "shots_on_target": shots_on_target[trailing_index] if shots_on_target and shots_on_target[trailing_index] is not None else math.nan,
    }
    
    # Формула доминирования
    xg_component = 0.0
    if not math.isnan(leader_metrics["xg"]) and not math.isnan(trailing_metrics["xg"]):
        xg_diff = leader_metrics["xg"] - trailing_metrics["xg"]
        xg_component = max(xg_diff * 3, 0)
    
    possession_component = 0.0
    if not math.isnan(leader_metrics["possession"]) and not math.isnan(trailing_metrics["possession"]):
        poss_diff = leader_metrics["possession"] - trailing_metrics["possession"]
        possession_component = max(poss_diff * 0.15, 0)
    
    shots_total_component = 0.0
    if not math.isnan(leader_metrics["shots_total"]) and not math.isnan(trailing_metrics["shots_total"]):
        shots_diff = leader_metrics["shots_total"] - trailing_metrics["shots_total"]
        shots_total_component = max(shots_diff * 0.3, 0)
    
    sot_component = 0.0
    if not math.isnan(leader_metrics["shots_on_target"]) and not math.isnan(trailing_metrics["shots_on_target"]):
        sot_diff = leader_metrics["shots_on_target"] - trailing_metrics["shots_on_target"]
        sot_component = max(sot_diff * 1.5, 0)
    
    dominance_score = xg_component + possession_component + shots_total_component + sot_component
    
    print(f"\nРасчет доминирования:")
    print(f"  xG компонент: {xg_component:.2f}")
    print(f"  Владение компонент: {possession_component:.2f}")
    print(f"  Удары компонент: {shots_total_component:.2f}")
    print(f"  Удары в створ компонент: {sot_component:.2f}")
    print(f"  ИТОГО доминирование: {dominance_score:.2f}")

