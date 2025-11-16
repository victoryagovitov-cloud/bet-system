#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_tennis_analyzer import analyze_live_tennis_matches, _is_allowed_tennis_tournament

print("=" * 60)
print("ПРОВЕРКА ТЕННИСА")
print("=" * 60)

# Получаем все live матчи через GraphQL
all_matches = fetch_live_matches(limit=50, sport="tennis")
print(f"\nВсего live матчей через GraphQL: {len(all_matches)}")

if all_matches:
    print("\nПервые 15 матчей:")
    for i, m in enumerate(all_matches[:15], 1):
        home = m.get("home_name", "?")
        away = m.get("away_name", "?")
        tournament = m.get("tournament_name", "N/A")
        allowed = _is_allowed_tennis_tournament(tournament)
        status = "[OK]" if allowed else "[FILTERED]"
        print(f"  {i}. {status} {home} vs {away}")
        print(f"      Турнир: {tournament}")
        print(f"      Разрешен: {allowed}")
else:
    print("Нет live матчей через GraphQL!")

print("\n" + "=" * 60)
print("ПРОВЕРКА ЧЕРЕЗ analyze_live_tennis_matches")
print("=" * 60)

analyzed = analyze_live_tennis_matches(limit=50)
print(f"\nПосле анализа: {len(analyzed)} матчей")

if analyzed:
    print("\nНайденные матчи:")
    for i, m in enumerate(analyzed[:10], 1):
        teams = m.get("teams", ["?", "?"])
        sets = m.get("sets_score", "?")
        dominance = m.get("dominance_score", 0)
        print(f"  {i}. {teams[0]} vs {teams[1]}: {sets} (dominance: {dominance:.1f})")
else:
    print("\nНет матчей после анализа!")
    print("\nПроверяю причины...")
    
    # Проверяем детально первые 5 матчей
    for m in all_matches[:5]:
        home = m.get("home_name", "?")
        away = m.get("away_name", "?")
        tournament = m.get("tournament_name", "N/A")
        slug = m.get("slug", "?")
        
        print(f"\n  Матч: {home} vs {away}")
        print(f"    Турнир: {tournament}")
        print(f"    Slug: {slug}")
        
        # Проверяем статистику
        try:
            stats = fetch_match_stats(slug, sport="tennis")
            print(f"    Статистика получена: {stats is not None}")
            if stats:
                result_scores = stats.get("result_scores", [])
                print(f"    Сеты: {len(result_scores)}")
        except Exception as e:
            print(f"    Ошибка получения статистики: {e}")

