#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_basketball_analyzer import analyze_live_basketball_matches

print("=" * 70)
print("ДЕТАЛЬНАЯ ПРОВЕРКА БАСКЕТБОЛА")
print("=" * 70)

# 1. Проверяем raw матчи
print("\n1. Live матчи на Scores24:")
raw_matches = fetch_live_matches(limit=20, sport="basketball")
print(f"   Найдено: {len(raw_matches)} матчей")

if raw_matches:
    print("\n   Первые 5 матчей:")
    for i, m in enumerate(raw_matches[:5], 1):
        teams = m.get("teams", [])
        home = teams[0].get("name", "?") if teams else "?"
        away = teams[1].get("name", "?") if len(teams) > 1 else "?"
        tournament = m.get("tournament_name", "?")
        minute = m.get("minute", "?")
        print(f"   {i}. {tournament}: {home} vs {away} (минута: {minute})")
else:
    print("   [ПРОБЛЕМА] Нет live матчей на Scores24")
    exit(0)

# 2. Проверяем проанализированные матчи
print("\n2. Проанализированные матчи:")
analyzed = analyze_live_basketball_matches(limit=20)
print(f"   Найдено: {len(analyzed)} матчей")

if analyzed:
    print("\n   Первые 3 матча:")
    for i, m in enumerate(analyzed[:3], 1):
        teams = m.get("teams", [])
        home = teams[0] if teams else "?"
        away = teams[1] if len(teams) > 1 else "?"
        score = m.get("score", "?")
        minute = m.get("minute", "?")
        dominance = m.get("dominance_score", 0)
        print(f"   {i}. {home} vs {away} | {score} ({minute}) | dominance: {dominance:.1f}")
else:
    print("   [ПРОБЛЕМА] Матчи не прошли фильтры анализатора")

# 3. Детальная проверка фильтрации
print("\n3. Детальная проверка фильтрации (первые 3 матча):")
MINIMUM_MINUTE_THRESHOLD = 3  # Снижено для баскетбола

for i, match in enumerate(raw_matches[:3], 1):
    slug = match.get("slug", "?")
    teams = match.get("teams", [])
    home = teams[0].get("name", "?") if teams else "?"
    away = teams[1].get("name", "?") if len(teams) > 1 else "?"
    
    print(f"\n   Матч {i}: {home} vs {away}")
    print(f"   Slug: {slug}")
    
    try:
        details = fetch_match_stats(slug, sport="basketball")
        
        # Проверяем минуты
        minute = details.get("minute")
        print(f"   Minute: {minute}")
        
        # Парсим минуты
        minute_numeric = None
        if minute:
            import re
            text = str(minute).strip().lower()
            match_obj = re.search(r"(\d+)", text)
            if match_obj:
                minute_numeric = int(match_obj.group(1))
        
        print(f"   Minute numeric: {minute_numeric}")
        
        if minute_numeric is None:
            print(f"   [FILTERED] Нет минут")
            continue
        
        if minute_numeric < MINIMUM_MINUTE_THRESHOLD:
            print(f"   [FILTERED] Минута {minute_numeric} < {MINIMUM_MINUTE_THRESHOLD}")
            continue
        
        if minute_numeric >= 40:
            print(f"   [FILTERED] Матч закончен (минута {minute_numeric} >= 40)")
            continue
        
        # Проверяем счет
        game_state = details.get("game_state", {})
        home_score = game_state.get("home_score")
        away_score = game_state.get("away_score")
        
        result_score = details.get("result_score")
        game_score = details.get("game_score")
        
        print(f"   Score (game_state): {home_score}:{away_score}")
        print(f"   Score (result_score): {result_score}")
        print(f"   Score (game_score): {game_score}")
        
        if home_score is None or away_score is None:
            # Пробуем парсить из result_score или game_score
            score = None
            if result_score:
                try:
                    parts = str(result_score).replace(" ", "").split(":")
                    if len(parts) == 2:
                        score = (int(parts[0]), int(parts[1]))
                except:
                    pass
            if not score and game_score:
                try:
                    parts = str(game_score).replace(" ", "").split(":")
                    if len(parts) == 2:
                        score = (int(parts[0]), int(parts[1]))
                except:
                    pass
            
            if score:
                home_score, away_score = score
                print(f"   Score parsed: {home_score}:{away_score}")
            else:
                print(f"   [FILTERED] Нет счета")
                continue
        else:
            home_score = int(home_score)
            away_score = int(away_score)
        
        if home_score == away_score:
            print(f"   [FILTERED] Ничья ({home_score}:{away_score})")
            continue
        
        # Проверяем статистику
        statistic = details.get("statistic")
        has_stats = False
        points = None
        
        if statistic and statistic.get("periods"):
            periods = statistic.get("periods", [])
            print(f"   Статистика: {len(periods)} период(ов)")
            
            # Ищем points
            for period in periods:
                groups = period.get("groups", [])
                for group in groups:
                    items = group.get("items", [])
                    for item in items:
                        item_type = item.get("type", "").lower()
                        item_name = item.get("name", "").lower()
                        
                        if "point" in item_type or "point" in item_name or "очк" in item_name:
                            home_val = item.get("team1_value")
                            away_val = item.get("team2_value")
                            if home_val is not None and away_val is not None:
                                points = (float(home_val), float(away_val))
                                has_stats = True
                                print(f"   [OK] Points найдены: {points}")
                                break
        
        if not points:
            # Используем счет как points
            points = (float(home_score), float(away_score))
            print(f"   [FALLBACK] Используем счет как points: {points}")
        
        # Проверяем dominance
        leader_index = 0 if home_score > away_score else 1
        score_diff = abs(home_score - away_score)
        
        print(f"   Score diff: {score_diff}")
        print(f"   Leader index: {leader_index}")
        
        # Простой расчет dominance для проверки
        time_factor = minute_numeric / 40.0
        score_factor = score_diff * 1.5
        points_component = abs(points[0] - points[1]) * 0.3
        
        simple_dominance = points_component + score_factor * time_factor
        print(f"   Simple dominance: {simple_dominance:.1f}")
        
        print(f"   [OK] ПРОШЕЛ БАЗОВЫЕ ФИЛЬТРЫ")
        
    except Exception as e:
        print(f"   [ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)

