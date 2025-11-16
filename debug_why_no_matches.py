#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from generate_live_report import generate_live_report
from graphql_live_analyzer import analyze_live_matches
from graphql_tennis_analyzer import analyze_live_tennis_matches
from graphql_basketball_analyzer import analyze_live_basketball_matches
from graphql_handball_analyzer import analyze_live_handball_matches
from generate_live_report import _get_recent_slugs, _filter_duplicates

print("=" * 70)
print("ДИАГНОСТИКА: ПОЧЕМУ МАТЧИ НЕ НАХОДЯТСЯ")
print("=" * 70)

# Шаг 1: Проверяем базовый анализ
print("\nШАГ 1: БАЗОВЫЙ АНАЛИЗ (БЕЗ ФИЛЬТРОВ ПО КОЭФФИЦИЕНТАМ)")
print("-" * 70)

football_raw = analyze_live_matches(limit=50)
print(f"Футбол (после базового анализа): {len(football_raw)} матчей")

tennis_raw = analyze_live_tennis_matches(limit=50)
print(f"Теннис (после базового анализа): {len(tennis_raw)} матчей")

basketball_raw = analyze_live_basketball_matches(limit=50)
print(f"Баскетбол (после базового анализа): {len(basketball_raw)} матчей")

handball_raw = analyze_live_handball_matches(limit=50)
print(f"Гандбол (после базового анализа): {len(handball_raw)} матчей")

total_raw = len(football_raw) + len(tennis_raw) + len(basketball_raw) + len(handball_raw)
print(f"\nВСЕГО матчей после базового анализа: {total_raw}")

if total_raw == 0:
    print("\n[ПРОБЛЕМА] Нет матчей даже после базового анализа!")
    print("Возможные причины:")
    print("  - Нет live матчей на Scores24")
    print("  - Матчи не имеют статистики")
    print("  - Матчи отфильтрованы как молодежные/дружеские")
    exit(0)

# Шаг 2: Проверяем фильтры по коэффициентам
print("\n" + "=" * 70)
print("ШАГ 2: ПРОВЕРКА ФИЛЬТРОВ ПО КОЭФФИЦИЕНТАМ")
print("-" * 70)

from generate_live_report import (
    _select_top_matches, _select_top_tennis_matches,
    _select_top_basketball_matches, _select_top_handball_matches,
    MIN_ODDS, PRIMARY_MAX_ODDS, EXTENDED_MAX_ODDS
)

football_filtered = _select_top_matches(limit=10)
print(f"Футбол (после фильтров по коэффициентам): {len(football_filtered)} матчей")

tennis_filtered = _select_top_tennis_matches(limit=10)
print(f"Теннис (после фильтров по коэффициентам): {len(tennis_filtered)} матчей")

basketball_filtered = _select_top_basketball_matches(limit=10)
print(f"Баскетбол (после фильтров по коэффициентам): {len(basketball_filtered)} матчей")

handball_filtered = _select_top_handball_matches(limit=10)
print(f"Гандбол (после фильтров по коэффициентам): {len(handball_filtered)} матчей")

total_filtered = len(football_filtered) + len(tennis_filtered) + len(basketball_filtered) + len(handball_filtered)
print(f"\nВСЕГО матчей после фильтров по коэффициентам: {total_filtered}")

if total_filtered == 0 and total_raw > 0:
    print("\n[ПРОБЛЕМА] Матчи отфильтрованы на этапе коэффициентов!")
    print(f"Настройки фильтров:")
    print(f"  MIN_ODDS = {MIN_ODDS}")
    print(f"  PRIMARY_MAX_ODDS = {PRIMARY_MAX_ODDS}")
    print(f"  EXTENDED_MAX_ODDS = {EXTENDED_MAX_ODDS}")
    
    # Показываем примеры матчей, которые не прошли
    if len(football_raw) > 0:
        print(f"\nПример футбольного матча (не прошел фильтры):")
        match = football_raw[0]
        print(f"  {match.get('teams', ['?', '?'])[0]} - {match.get('teams', ['?', '?'])[1]}")
        print(f"  Dominance: {match.get('dominance_score', '?')}")
        print(f"  Минута: {match.get('minute_numeric', '?')}")

# Шаг 3: Проверяем дедупликацию
print("\n" + "=" * 70)
print("ШАГ 3: ПРОВЕРКА ДЕДУПЛИКАЦИИ")
print("-" * 70)

recent_slugs = _get_recent_slugs(hours=4)
print(f"Недавно отправленных матчей (за 4 часа): {len(recent_slugs)}")

if total_filtered > 0:
    all_matches = football_filtered + tennis_filtered + basketball_filtered + handball_filtered
    after_dedup = _filter_duplicates(all_matches, recent_slugs)
    print(f"Матчей после дедупликации: {len(after_dedup)}")
    
    if len(after_dedup) == 0 and len(all_matches) > 0:
        print("\n[ПРОБЛЕМА] Все матчи отфильтрованы как дубликаты!")
        print("Недавно отправленные матчи:")
        for i, slug in enumerate(list(recent_slugs)[:5], 1):
            print(f"  {i}. {slug}")

# Шаг 4: Финальная проверка
print("\n" + "=" * 70)
print("ШАГ 4: ФИНАЛЬНАЯ ПРОВЕРКА (generate_live_report)")
print("-" * 70)

message, matches, context = generate_live_report(max_matches=5)
print(f"Финальный результат: {len(matches)} матчей")

if len(matches) == 0:
    print("\n[ВЫВОД] Матчи не найдены на этапе generate_live_report")
    print("\nКонтекст:")
    for key, value in context.items():
        if key != "generated_at":
            print(f"  {key}: {value}")
else:
    print("\n[OK] Матчи найдены!")
    for i, match in enumerate(matches, 1):
        sport = match.get("sport", "unknown")
        teams = match.get("teams", ["?", "?"])
        odds = match.get("odds_info", {}).get("value") if hasattr(match.get("odds_info", {}), "value") else match.get("odds", {}).get("value", "?")
        print(f"\n{i}. {sport.upper()}: {teams[0]} - {teams[1]}")
        print(f"   Коэффициент: {odds}, Dominance: {match.get('dominance_score', '?')}")

print("\n" + "=" * 70)
print("ДИАГНОСТИКА ЗАВЕРШЕНА")
print("=" * 70)

