#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats

print("=" * 70)
print("АНАЛИЗ ДОСТУПНОСТИ СТАТИСТИКИ И ПРОГНОЗИРУЕМОСТИ")
print("=" * 70)

sports_to_check = [
    ("hockey", "Хоккей"),
    ("volleyball", "Волейбол"),
    ("table-tennis", "Настольный теннис"),
]

for sport_slug, sport_name in sports_to_check:
    print(f"\n{'='*70}")
    print(f"{sport_name.upper()} ({sport_slug})")
    print(f"{'='*70}")
    
    # Проверяем наличие live матчей
    raw_matches = fetch_live_matches(limit=10, sport=sport_slug)
    print(f"\n1. Live матчей на Scores24: {len(raw_matches)}")
    
    if len(raw_matches) == 0:
        print("   [SKIP] Нет live матчей - пропускаем")
        continue
    
    # Проверяем статистику для первых 3 матчей
    print(f"\n2. Проверка статистики (первые {min(3, len(raw_matches))} матча):")
    
    stats_available = {
        "score": 0,
        "minute": 0,
        "possession": 0,
        "shots": 0,
        "points": 0,
        "sets": 0,
        "statistic": 0,
    }
    
    for i, match in enumerate(raw_matches[:3], 1):
        slug = match.get("slug", "?")
        teams = match.get("teams", [])
        home = teams[0].get("name", "?") if teams else "?"
        away = teams[1].get("name", "?") if len(teams) > 1 else "?"
        
        print(f"\n   Матч {i}: {home} vs {away}")
        print(f"   Slug: {slug}")
        
        try:
            details = fetch_match_stats(slug, sport=sport_slug)
            
            # Проверяем счет
            game_score = details.get("game_score")
            result_score = details.get("result_score")
            game_state = details.get("game_state", {})
            home_score = game_state.get("home_score")
            away_score = game_state.get("away_score")
            
            if game_score or result_score or (home_score is not None and away_score is not None):
                stats_available["score"] += 1
                print(f"   [OK] Счет: {game_score or result_score or f'{home_score}:{away_score}'}")
            else:
                print(f"   [FAIL] Нет счета")
            
            # Проверяем минуты/периоды
            minute = details.get("minute")
            if minute:
                stats_available["minute"] += 1
                print(f"   [OK] Минута: {minute}")
            else:
                print(f"   [FAIL] Нет минут")
            
            # Проверяем статистику
            statistic = details.get("statistic")
            if statistic and statistic.get("periods"):
                stats_available["statistic"] += 1
                periods = statistic.get("periods", [])
                print(f"   [OK] Статистика: {len(periods)} период(ов)")
                
                # Проверяем конкретные метрики
                for period in periods:
                    groups = period.get("groups", [])
                    for group in groups:
                        items = group.get("items", [])
                        for item in items:
                            item_type = item.get("type", "").lower()
                            item_name = item.get("name", "").lower()
                            
                            if "possession" in item_type or "possession" in item_name or "владение" in item_name:
                                stats_available["possession"] += 1
                            if "shot" in item_type or "shot" in item_name or "удар" in item_name or "бросок" in item_name:
                                stats_available["shots"] += 1
                            if "point" in item_type or "point" in item_name or "очк" in item_name:
                                stats_available["points"] += 1
                            if "set" in item_type or "set" in item_name or "сет" in item_name:
                                stats_available["sets"] += 1
            else:
                print(f"   [FAIL] Нет статистики")
                
        except Exception as e:
            print(f"   [ERROR] Ошибка: {e}")
    
    # Итоговая оценка
    print(f"\n3. ИТОГОВАЯ ОЦЕНКА:")
    total_checked = min(3, len(raw_matches))
    
    score_pct = (stats_available["score"] / total_checked * 100) if total_checked > 0 else 0
    minute_pct = (stats_available["minute"] / total_checked * 100) if total_checked > 0 else 0
    stats_pct = (stats_available["statistic"] / total_checked * 100) if total_checked > 0 else 0
    
    print(f"   Счет: {stats_available['score']}/{total_checked} ({score_pct:.0f}%)")
    print(f"   Минуты: {stats_available['minute']}/{total_checked} ({minute_pct:.0f}%)")
    print(f"   Статистика: {stats_available['statistic']}/{total_checked} ({stats_pct:.0f}%)")
    
    if stats_available["possession"] > 0:
        print(f"   - Владение найдено: {stats_available['possession']} раз")
    if stats_available["shots"] > 0:
        print(f"   - Удары/броски найдены: {stats_available['shots']} раз")
    if stats_available["points"] > 0:
        print(f"   - Очки найдены: {stats_available['points']} раз")
    if stats_available["sets"] > 0:
        print(f"   - Сеты найдены: {stats_available['sets']} раз")
    
    # Рекомендация
    print(f"\n4. РЕКОМЕНДАЦИЯ:")
    if score_pct >= 80 and minute_pct >= 80 and stats_pct >= 60:
        print(f"   [RECOMMENDED] Хорошая доступность статистики - стоит добавить")
    elif score_pct >= 60 and minute_pct >= 60:
        print(f"   [CONSIDER] Средняя доступность - можно рассмотреть")
    else:
        print(f"   [NOT RECOMMENDED] Низкая доступность статистики - не стоит добавлять")

print("\n" + "=" * 70)

