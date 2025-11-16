#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches, fetch_match_stats
from graphql_basketball_analyzer import _parse_score, _extract_totals, _parse_minute_value, _is_tournament_allowed, _is_youth_team, MINIMUM_MINUTE_THRESHOLD

print("=" * 70)
print("ДЕТАЛЬНАЯ ДИАГНОСТИКА БАСКЕТБОЛА")
print("=" * 70)

all_matches = fetch_live_matches(limit=50, sport="basketball")
print(f"\nВсего live матчей: {len(all_matches)}")

if len(all_matches) == 0:
    print("Нет матчей")
    exit(0)

# Проверяем первые 5 матчей детально
for i, match_info in enumerate(all_matches[:5], 1):
    slug = match_info.get("slug", "")
    teams = match_info.get("teams", [])
    home = teams[0].get("name", "?") if len(teams) > 0 else "?"
    away = teams[1].get("name", "?") if len(teams) > 1 else "?"
    
    print(f"\n{'='*70}")
    print(f"МАТЧ {i}: {home} - {away}")
    print(f"{'='*70}")
    
    try:
        details = fetch_match_stats(slug, sport="basketball")
        
        # Проверка 1: Счет
        score = _parse_score(details)
        if not score:
            print("[ОТФИЛЬТРОВАН] Нет счета")
            continue
        home_score, away_score = score
        print(f"Счет: {home_score}:{away_score}")
        
        if home_score == away_score:
            print("[ОТФИЛЬТРОВАН] Ничья")
            continue
        
        # Проверка 2: Статистика (используем счет как очки, если статистики нет)
        totals = _extract_totals(details.get("statistic"))
        points = totals.get("points") or totals.get("очки")
        
        print(f"Статистика points из totals: {points}")
        
        # Если нет статистики points, используем счет (как в исправленном коде)
        if not points or points[0] is None or points[1] is None:
            points = (float(home_score), float(away_score))
            print(f"  Используем счет как очки: {points}")
        else:
            print(f"  Очки из статистики: {points[0]} - {points[1]}")
        
        # Проверка 3: Минуты
        raw_minute = details.get("minute")
        if raw_minute is None:
            raw_minute = match_info.get("minute")
        minute_numeric = _parse_minute_value(details.get("minute"))
        if minute_numeric is None:
            minute_numeric = _parse_minute_value(match_info.get("minute"))
        
        print(f"Минута: {raw_minute} (numeric: {minute_numeric})")
        
        if minute_numeric is not None and minute_numeric < MINIMUM_MINUTE_THRESHOLD:
            print(f"[ОТФИЛЬТРОВАН] Слишком рано ({minute_numeric} < {MINIMUM_MINUTE_THRESHOLD})")
            continue
        
        if minute_numeric is not None and minute_numeric >= 40:
            print("[ОТФИЛЬТРОВАН] Матч закончен (>= 40 минут)")
            continue
        
        # Проверка 4: Турнир
        tournament = (
            (details.get("unique_tournament") or {}).get("name")
            or details.get("tournament_name")
            or match_info.get("tournament_name")
            or match_info.get("league_slug")
        )
        print(f"Турнир: {tournament}")
        
        if not _is_tournament_allowed(tournament):
            print("[ОТФИЛЬТРОВАН] Турнир не разрешен")
            continue
        
        # Проверка 5: Молодежные команды
        if _is_youth_team(home) or _is_youth_team(away):
            print(f"[ОТФИЛЬТРОВАН] Молодежная команда")
            continue
        
        # Проверка 6: Команды
        teams_list = details.get("teams") or []
        if len(teams_list) < 2:
            print("[ОТФИЛЬТРОВАН] Недостаточно команд")
            continue
        
        home_name = teams_list[0].get("name")
        away_name = teams_list[1].get("name")
        
        print(f"Команды: {home_name} - {away_name}")
        
        # Если дошли сюда - матч должен пройти
        print("[OK] Матч должен пройти базовый анализ!")
        
    except Exception as e:
        print(f"[ОШИБКА] {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("ДИАГНОСТИКА ЗАВЕРШЕНА")
print("=" * 70)

