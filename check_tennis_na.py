#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_tennis_analyzer import analyze_live_tennis_matches

print("Проверка теннисных матчей с N/A:")
print("=" * 60)

# Получаем все лайв матчи
all_tennis = fetch_live_matches(limit=20, sport="tennis")
print(f"Всего лайв матчей: {len(all_tennis)}")

# Группируем по названию турнира
by_tournament = {}
for match in all_tennis:
    tournament = match.get("tournament_name") or match.get("category_name") or "N/A"
    by_tournament.setdefault(tournament, []).append(match)

print(f"\nТурниры:")
for name, matches in sorted(by_tournament.items(), key=lambda x: -len(x[1])):
    print(f"  {name}: {len(matches)} матчей")

# Проверяем матчи с N/A
na_matches = by_tournament.get("N/A", [])
print(f"\nМатчей с N/A: {len(na_matches)}")

if len(na_matches) > 0:
    print("\nПроверяем первый матч с N/A:")
    first_na = na_matches[0]
    slug = first_na.get('slug')
    try:
        details = fetch_match_stats(slug, sport="tennis")
        tournament_name = (
            (details.get("unique_tournament") or {}).get("name")
            or details.get("tournament_name")
            or first_na.get("tournament_name")
            or first_na.get("category_name")
        )
        print(f"  Slug: {slug}")
        print(f"  Название турнира из details: {tournament_name}")
        print(f"  Статус: {(details.get('status') or {}).get('code')}")
        print(f"  Счет: {details.get('result_score')}")
    except Exception as e:
        print(f"  Ошибка: {e}")

# Пробуем проанализировать
print("\n" + "=" * 60)
analyzed = analyze_live_tennis_matches(limit=20)
print(f"Прошло анализ: {len(analyzed)} матчей")

