#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_live_analyzer import analyze_live_matches, _is_tournament_allowed, LOWER_DIVISION_KEYWORDS
from graphql_tennis_analyzer import analyze_live_tennis_matches, _is_allowed_tennis_tournament, ALLOWED_TENNIS_KEYWORDS, DISALLOWED_TENNIS_KEYWORDS
from scores24_graphql_client import fetch_live_matches

print("=" * 60)
print("ПРОВЕРКА ФИЛЬТРАЦИИ ТУРНИРОВ")
print("=" * 60)

# ФУТБОЛ
print("\n1. ФУТБОЛ - Проверка фильтрации молодежных турниров:")
print("-" * 60)

# Получаем все лайв матчи
all_football = fetch_live_matches(limit=100, sport="soccer")
print(f"Всего лайв матчей футбола: {len(all_football)}")

# Проверяем названия турниров
tournament_names = {}
for match in all_football:
    tournament = match.get("tournament_name") or match.get("category_name") or "N/A"
    tournament_names.setdefault(tournament, []).append(match)

print(f"\nУникальных турниров: {len(tournament_names)}")

# Ищем молодежные турниры
youth_tournaments = []
for name, matches in tournament_names.items():
    normalized = " ".join(name.lower().split()) if name else ""
    if any(kw in normalized for kw in LOWER_DIVISION_KEYWORDS):
        youth_tournaments.append((name, len(matches)))
        print(f"  [X] МОЛОДЕЖНЫЙ: {name} ({len(matches)} матчей)")

print(f"\nВсего молодежных турниров: {len(youth_tournaments)}")

# Проверяем, что фильтр работает
print("\nПроверка фильтра _is_tournament_allowed:")
test_names = [
    "Чемпионат Европы до 19 лет, квалификация",
    "Молодежная лига до 19",
    "Премьер-лига",
    "Лига чемпионов",
]
for name in test_names:
    allowed = _is_tournament_allowed(name)
    print(f"  {name}: {'[OK] РАЗРЕШЕН' if allowed else '[X] ЗАПРЕЩЕН'}")

# Анализируем матчи
analyzed = analyze_live_matches(limit=100)
print(f"\nПрошло фильтр и анализ: {len(analyzed)} матчей")

# Проверяем, есть ли молодежка в результатах
youth_in_results = []
for match in analyzed:
    tournament = match.get("tournament_name", "")
    normalized = " ".join(tournament.lower().split()) if tournament else ""
    if any(kw in normalized for kw in LOWER_DIVISION_KEYWORDS):
        youth_in_results.append((tournament, match.get("home_team"), match.get("away_team")))

if youth_in_results:
    print(f"\n[!] В РЕЗУЛЬТАТАХ ЕСТЬ МОЛОДЕЖКА ({len(youth_in_results)} матчей):")
    for tournament, home, away in youth_in_results[:5]:
        print(f"  - {tournament}: {home} vs {away}")
else:
    print("\n[OK] Молодежка отфильтрована корректно")

# ТЕННИС
print("\n\n2. ТЕННИС - Проверка фильтрации турниров:")
print("-" * 60)

# Получаем все лайв матчи тенниса
all_tennis = fetch_live_matches(limit=100, sport="tennis")
print(f"Всего лайв матчей тенниса: {len(all_tennis)}")

# Проверяем названия турниров
tennis_tournaments = {}
for match in all_tennis:
    tournament = match.get("tournament_name") or match.get("category_name") or "N/A"
    tennis_tournaments.setdefault(tournament, []).append(match)

print(f"\nУникальных турниров: {len(tennis_tournaments)}")

# Показываем топ-10 турниров
print("\nТоп-10 турниров по количеству матчей:")
for i, (name, matches) in enumerate(sorted(tennis_tournaments.items(), key=lambda x: -len(x[1]))[:10], 1):
    allowed = _is_allowed_tennis_tournament(name)
    status = "[OK] РАЗРЕШЕН" if allowed else "[X] ЗАПРЕЩЕН"
    print(f"  {i}. {name} ({len(matches)} матчей) - {status}")

# Проверяем, какие ключевые слова есть в разрешенных турнирах
print("\nПроверка ключевых слов в разрешенных турнирах:")
allowed_count = 0
disallowed_count = 0
unknown_count = 0

for name, matches in tennis_tournaments.items():
    if not name or name == "N/A":
        unknown_count += len(matches)
        continue
    if _is_allowed_tennis_tournament(name):
        allowed_count += len(matches)
        # Проверяем, какое ключевое слово сработало
        text = name.lower()
        matched_keywords = [kw for kw in ALLOWED_TENNIS_KEYWORDS if kw in text]
        if matched_keywords:
            print(f"  [OK] {name[:50]}: {matched_keywords}")
    else:
        disallowed_count += len(matches)

print(f"\nСтатистика:")
print(f"  Разрешенных: {allowed_count} матчей")
print(f"  Запрещенных: {disallowed_count} матчей")
print(f"  Без названия: {unknown_count} матчей")

# Анализируем матчи
analyzed_tennis = analyze_live_tennis_matches(limit=100)
print(f"\nПрошло фильтр и анализ: {len(analyzed_tennis)} матчей")

if len(analyzed_tennis) == 0:
    print("\n[!] ПРОБЛЕМА: Нет теннисных матчей в результатах!")
    print("\nВозможные причины:")
    print("  1. Слишком строгий фильтр турниров")
    print("  2. Нет подходящих матчей по статистике")
    print("  3. Все матчи не проходят критерии (сеты, геймы, статистика)")

print("\n" + "=" * 60)

