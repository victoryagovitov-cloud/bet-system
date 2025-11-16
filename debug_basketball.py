#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_basketball_analyzer import analyze_live_basketball_matches
from generate_live_report import _select_top_basketball_matches, _get_leader_odds, MIN_ODDS, PRIMARY_MAX_ODDS, EXTENDED_MAX_ODDS, EXTENDED_MIN_DOMINANCE
from scores24_graphql_client import fetch_live_matches

print("=" * 70)
print("ДИАГНОСТИКА БАСКЕТБОЛА")
print("=" * 70)

# Шаг 1: Проверяем, есть ли вообще live матчи по баскетболу
print("\nШАГ 1: ПРОВЕРКА LIVE МАТЧЕЙ НА SCORES24")
print("-" * 70)

try:
    all_basketball = fetch_live_matches(limit=100, sport="basketball")
    print(f"Всего live матчей по баскетболу на Scores24: {len(all_basketball)}")
    
    if len(all_basketball) == 0:
        print("\n[ВЫВОД] На Scores24 нет live матчей по баскетболу прямо сейчас")
        exit(0)
    
    # Показываем первые 5 матчей
    print("\nПервые 5 матчей:")
    for i, match in enumerate(all_basketball[:5], 1):
        teams = match.get("teams", [])
        home = teams[0].get("name", "?") if len(teams) > 0 else "?"
        away = teams[1].get("name", "?") if len(teams) > 1 else "?"
        minute = match.get("minute", "?")
        print(f"  {i}. {home} - {away} (минута: {minute})")
        
except Exception as e:
    print(f"Ошибка при получении матчей: {e}")
    exit(1)

# Шаг 2: Проверяем базовый анализ
print("\n" + "=" * 70)
print("ШАГ 2: БАЗОВЫЙ АНАЛИЗ (analyze_live_basketball_matches)")
print("-" * 70)

try:
    analyzed = analyze_live_basketball_matches(limit=50)
    print(f"Матчей после базового анализа: {len(analyzed)}")
    
    if len(analyzed) == 0:
        print("\n[ПРОБЛЕМА] Матчи отфильтрованы на этапе базового анализа")
        print("Возможные причины:")
        print("  - Нет статистики (points обязательны)")
        print("  - Матч слишком рано (< 15 минут)")
        print("  - Матч закончен (>= 40 минут)")
        print("  - Ничья (home_score == away_score)")
        print("  - Молодежные/дружеские турниры")
        print("  - Молодежные команды")
    else:
        print("\nПримеры проанализированных матчей:")
        for i, match in enumerate(analyzed[:3], 1):
            teams = match.get("teams", ["?", "?"])
            score = match.get("score", "?")
            minute = match.get("minute_numeric", "?")
            dominance = match.get("dominance_score", "?")
            print(f"\n  {i}. {teams[0]} - {teams[1]}")
            print(f"     Счет: {score}, Минута: {minute}, Dominance: {dominance:.2f}")
            
            # Проверяем статистику
            leader = match.get("leader_metrics", {})
            trailing = match.get("trailing_metrics", {})
            print(f"     Очки: {leader.get('points', '?')} - {trailing.get('points', '?')}")
            if not (leader.get('rebounds') is None or trailing.get('rebounds') is None):
                print(f"     Подборы: {leader.get('rebounds', '?')} - {trailing.get('rebounds', '?')}")
            
except Exception as e:
    print(f"Ошибка при анализе: {e}")
    import traceback
    traceback.print_exc()

# Шаг 3: Проверяем фильтры по коэффициентам
print("\n" + "=" * 70)
print("ШАГ 3: ФИЛЬТРЫ ПО КОЭФФИЦИЕНТАМ (_select_top_basketball_matches)")
print("-" * 70)

try:
    filtered = _select_top_basketball_matches(limit=10)
    print(f"Матчей после фильтров по коэффициентам: {len(filtered)}")
    
    if len(filtered) == 0 and len(analyzed) > 0:
        print("\n[ПРОБЛЕМА] Матчи отфильтрованы на этапе коэффициентов")
        print(f"Настройки фильтров:")
        print(f"  MIN_ODDS = {MIN_ODDS}")
        print(f"  PRIMARY_MAX_ODDS = {PRIMARY_MAX_ODDS}")
        print(f"  EXTENDED_MAX_ODDS = {EXTENDED_MAX_ODDS}")
        print(f"  EXTENDED_MIN_DOMINANCE = {EXTENDED_MIN_DOMINANCE}")
        
        # Проверяем первые 3 матча детально
        print("\nДетальная проверка первых 3 матчей:")
        for i, match in enumerate(analyzed[:3], 1):
            teams = match.get("teams", ["?", "?"])
            slug = match.get("slug", "")
            leader_index = match.get("leader_index", 0)
            dominance = match.get("dominance_score", 0)
            minute_numeric = match.get("minute_numeric", 0)
            
            print(f"\n  {i}. {teams[0]} - {teams[1]}")
            print(f"     Slug: {slug}")
            print(f"     Dominance: {dominance:.2f}, Минута: {minute_numeric}")
            
            # Пытаемся получить коэффициенты
            try:
                odds_info = _get_leader_odds(slug, leader_index, sport="basketball")
                if odds_info and odds_info.value:
                    odds = odds_info.value
                    print(f"     Коэффициент: {odds} (букмекер: {odds_info.bookmaker})")
                    
                    # Проверяем, почему не прошел
                    if odds < MIN_ODDS:
                        print(f"     [ОТФИЛЬТРОВАН] Коэффициент слишком низкий ({odds} < {MIN_ODDS})")
                    elif odds > EXTENDED_MAX_ODDS:
                        print(f"     [ОТФИЛЬТРОВАН] Коэффициент слишком высокий ({odds} > {EXTENDED_MAX_ODDS})")
                    else:
                        # Проверяем требования по dominance
                        if odds <= PRIMARY_MAX_ODDS:
                            if minute_numeric < 20:
                                required = 5.0
                            else:
                                required = 2.0
                            print(f"     PRIMARY tier: требуется dominance >= {required}")
                            if dominance < required:
                                print(f"     [ОТФИЛЬТРОВАН] Dominance {dominance:.2f} < {required}")
                        elif odds <= EXTENDED_MAX_ODDS:
                            if minute_numeric < 20:
                                required = 8.0
                            elif minute_numeric < 30:
                                required = EXTENDED_MIN_DOMINANCE
                            else:
                                required = 5.0
                            print(f"     EXTENDED tier: требуется dominance >= {required}")
                            if dominance < required:
                                print(f"     [ОТФИЛЬТРОВАН] Dominance {dominance:.2f} < {required}")
                else:
                    print(f"     [ОТФИЛЬТРОВАН] Нет коэффициентов")
            except Exception as e:
                print(f"     [ОШИБКА] Не удалось получить коэффициенты: {e}")
    else:
        print("\n[OK] Матчи прошли фильтры по коэффициентам!")
        for i, match in enumerate(filtered[:3], 1):
            teams = match.get("teams", ["?", "?"])
            odds = match.get("odds_info", {}).get("value") if hasattr(match.get("odds_info", {}), "value") else "?"
            dominance = match.get("dominance_score", "?")
            print(f"  {i}. {teams[0]} - {teams[1]} (кэф: {odds}, dominance: {dominance})")
            
except Exception as e:
    print(f"Ошибка при фильтрации: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("ДИАГНОСТИКА ЗАВЕРШЕНА")
print("=" * 70)

