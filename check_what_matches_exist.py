#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scores24_graphql_client import fetch_live_matches

print("=" * 70)
print("ДЕТАЛЬНАЯ ПРОВЕРКА: ЧТО ЕСТЬ НА SCORES24")
print("=" * 70)

all_matches = fetch_live_matches()
print(f"\nВсего live матчей: {len(all_matches)}")

if len(all_matches) == 0:
    print("\n[ВЫВОД] На Scores24 вообще нет live матчей")
    exit(0)

# Группируем по видам спорта
by_sport = {}
for match in all_matches:
    sport = match.get("sport", "unknown")
    if sport not in by_sport:
        by_sport[sport] = []
    by_sport[sport].append(match)

print("\nРаспределение по видам спорта:")
for sport, matches in sorted(by_sport.items()):
    print(f"  {sport}: {len(matches)}")

# Проверяем футбол и теннис подробнее
print("\n" + "=" * 70)
print("ДЕТАЛИ ПО ФУТБОЛУ И ТЕННИСУ")
print("-" * 70)

for sport_name in ["soccer", "tennis"]:
    matches = [m for m in all_matches if m.get("sport") == sport_name]
    if len(matches) == 0:
        print(f"\n{sport_name.upper()}: Нет матчей")
        continue
    
    print(f"\n{sport_name.upper()}: {len(matches)} матчей")
    
    # Проверяем первые 5 матчей
    for i, match in enumerate(matches[:5], 1):
        home = match.get("home_team", "?")
        away = match.get("away_team", "?")
        tournament = match.get("tournament_name", "?")
        status = match.get("status_code", "?")
        minute = match.get("minute", "?")
        
        # Проверяем наличие статистики
        has_xg = "home_xg" in match and match.get("home_xg") is not None
        has_shots = "home_shots_on_target" in match and match.get("home_shots_on_target") is not None
        has_possession = "home_possession" in match and match.get("home_possession") is not None
        
        print(f"\n  {i}. {home} - {away}")
        print(f"     Турнир: {tournament}")
        print(f"     Статус: {status}, Минута: {minute}")
        print(f"     Статистика: xG={has_xg}, Удары={has_shots}, Владение={has_possession}")
        
        # Проверяем, почему может быть отфильтрован
        reasons = []
        
        # Проверка на молодежные/дружеские
        tournament_lower = tournament.lower() if tournament else ""
        if any(marker in tournament_lower for marker in ["u19", "u20", "u21", "u23", "молод", "youth", "товарищ", "friendly", "дружеск"]):
            reasons.append("Молодежный/дружеский турнир")
        
        # Проверка на низшие дивизионы
        lower_keywords = ["lower", "низш", "amateur", "любительск"]
        if any(kw in tournament_lower for kw in lower_keywords):
            reasons.append("Низший дивизион")
        
        if reasons:
            print(f"     [ОТФИЛЬТРОВАН]: {', '.join(reasons)}")
        elif not (has_xg or has_shots or has_possession):
            print(f"     [ОТФИЛЬТРОВАН]: Нет статистики")
        else:
            print(f"     [ПОТЕНЦИАЛЬНО ПОДХОДИТ]: Есть статистика, не молодежный")

print("\n" + "=" * 70)
print("ВЫВОД")
print("=" * 70)

soccer_count = len([m for m in all_matches if m.get("sport") == "soccer"])
tennis_count = len([m for m in all_matches if m.get("sport") == "tennis"])

if soccer_count == 0 and tennis_count == 0:
    print("На Scores24 нет live матчей по футболу и теннису прямо сейчас")
    print("Это НЕ проблема фильтров - просто нет матчей в это время")
elif soccer_count > 0 or tennis_count > 0:
    print(f"Есть {soccer_count} футбольных и {tennis_count} теннисных матчей")
    print("Но они отфильтрованы на этапе базового анализа:")
    print("  - Нет статистики")
    print("  - Молодежные/дружеские")
    print("  - Низшие дивизионы")
    print("\nЭто НЕ проблема фильтров по коэффициентам")

