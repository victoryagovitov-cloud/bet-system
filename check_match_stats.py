#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats

print("=" * 70)
print("ПРОВЕРКА: ЕСТЬ ЛИ СТАТИСТИКА У МАТЧЕЙ")
print("=" * 70)

all_matches = fetch_live_matches()
print(f"\nВсего live матчей: {len(all_matches)}")

if len(all_matches) == 0:
    print("Нет матчей")
    exit(0)

# Проверяем первые 5 матчей
matches_with_stats = 0
matches_without_stats = 0
filtered_reasons = []

for i, match_info in enumerate(all_matches[:5], 1):
    slug = match_info.get("slug", "")
    teams = match_info.get("teams", [])
    home = teams[0].get("name", "?") if len(teams) > 0 else "?"
    away = teams[1].get("name", "?") if len(teams) > 1 else "?"
    league = match_info.get("league_slug", "?")
    
    print(f"\n{i}. {home} - {away}")
    print(f"   League: {league}")
    
    try:
        details = fetch_match_stats(slug)
        
        # Проверяем наличие статистики
        stats = details.get("statistic", {})
        totals = stats.get("totals", []) if isinstance(stats, dict) else []
        
        # Ищем нужные метрики
        has_xg = False
        has_possession = False
        has_shots = False
        
        for total in totals:
            if isinstance(total, dict):
                name = total.get("name", "").lower()
                if "xg" in name or "expected goals" in name:
                    has_xg = True
                if "possession" in name or "ball possession" in name:
                    has_possession = True
                if "shots on target" in name or "shots on goal" in name:
                    has_shots = True
        
        # Проверяем score
        score = details.get("game_score")
        if score:
            home_score = score.get("home", 0)
            away_score = score.get("away", 0)
            if home_score == away_score:
                print(f"   [ОТФИЛЬТРОВАН]: Ничья ({home_score}:{away_score})")
                filtered_reasons.append("ничья")
                continue
        
        # Проверяем турнир
        tournament = (
            (details.get("unique_tournament") or {}).get("name")
            or details.get("tournament_name")
            or match_info.get("tournament_name")
            or match_info.get("league_slug", "")
        )
        
        tournament_lower = (tournament or "").lower()
        is_friendly = any(kw in tournament_lower for kw in ["friendly", "дружеск", "товарищ"])
        is_youth = any(kw in tournament_lower for kw in ["u18", "u19", "u20", "u21", "молод", "youth"])
        
        if is_friendly:
            print(f"   [ОТФИЛЬТРОВАН]: Дружеский матч")
            filtered_reasons.append("дружеский")
            continue
        if is_youth:
            print(f"   [ОТФИЛЬТРОВАН]: Молодежный турнир")
            filtered_reasons.append("молодежный")
            continue
        
        print(f"   Статистика: xG={has_xg}, Владение={has_possession}, Удары={has_shots}")
        
        # Проверяем, достаточно ли статистики
        if has_possession and has_shots:
            print(f"   [OK] Есть минимальная статистика (владение + удары)")
            matches_with_stats += 1
        elif has_xg:
            print(f"   [OK] Есть xG")
            matches_with_stats += 1
        else:
            print(f"   [ОТФИЛЬТРОВАН]: Нет нужной статистики")
            matches_without_stats += 1
            filtered_reasons.append("нет статистики")
            
    except Exception as e:
        print(f"   [ОШИБКА] Не удалось получить статистику: {e}")
        matches_without_stats += 1
        filtered_reasons.append("ошибка получения")

print("\n" + "=" * 70)
print("ИТОГИ")
print("=" * 70)
print(f"Матчей с достаточной статистикой: {matches_with_stats}")
print(f"Матчей без статистики/отфильтрованных: {matches_without_stats}")

if matches_with_stats == 0:
    print("\n[ВЫВОД] Проблема НЕ в жестких фильтрах по коэффициентам")
    print("Проблема в том, что:")
    print("  - Матчи не имеют статистики (xG, владение, удары)")
    print("  - Или матчи отфильтрованы как дружеские/молодежные")
    print("\nЭто означает, что сейчас действительно мало подходящих матчей")
else:
    print(f"\n[ВЫВОД] Есть {matches_with_stats} матчей с статистикой")
    print("Но они могут не проходить фильтры по коэффициентам")

