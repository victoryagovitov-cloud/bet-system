#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_live_analyzer import analyze_live_matches
from generate_live_report import _get_recent_slugs, _filter_duplicates, _select_top_matches
from scores24_graphql_client import fetch_match_odds

print("=" * 60)
print("ДЕТАЛЬНАЯ ПРОВЕРКА ФУТБОЛА")
print("=" * 60)

# Получаем все проанализированные матчи
analyzed = analyze_live_matches(limit=120)
print(f"\nПосле analyze_live_matches: {len(analyzed)} матчей")

if analyzed:
    print("\nДетали найденных матчей:")
    for i, m in enumerate(analyzed[:5]):
        teams = m.get("teams", [])
        print(f"\n{i+1}. {teams[0] if teams else '?'} - {teams[1] if len(teams) > 1 else '?'}")
        print(f"   Slug: {m.get('slug', '?')}")
        print(f"   Счет: {m.get('score', '?')}")
        print(f"   Минута: {m.get('minute_numeric', '?')}")
        print(f"   Доминирование: {m.get('dominance_score', 0):.2f}")
        print(f"   xG: {m.get('xg', 'отсутствует')}")
        print(f"   Владение: {m.get('possession', '?')}")
        print(f"   Удары в створ: {m.get('shots_on_target', '?')}")

# Проверяем отбор топ-матчей
print("\n" + "=" * 60)
print("ПРОВЕРКА _select_top_matches:")
print("=" * 60)

top_matches = _select_top_matches(limit=5)
print(f"После _select_top_matches: {len(top_matches)} матчей")

if top_matches:
    print("\nДетали топ-матчей:")
    for i, m in enumerate(top_matches):
        teams = m.get("teams", [])
        odds = m.get("odds_info")
        odds_value = odds.value if odds else None
        print(f"\n{i+1}. {teams[0] if teams else '?'} - {teams[1] if len(teams) > 1 else '?'}")
        print(f"   Коэффициент: {odds_value}")
        print(f"   Доминирование: {m.get('dominance_score', 0):.2f}")
        print(f"   Счет: {m.get('score', '?')}")
        
        # Проверяем коэффициенты вручную
        slug = m.get("slug", "")
        leader_index = m.get("leader_index", 0)
        if slug:
            print(f"   Проверка коэффициентов для slug: {slug}")
            odds_markets = fetch_match_odds(slug, market=None, limit=5, market_limit=5, sport="soccer")
            desired_outcome = "w1" if leader_index == 0 else "w2"
            print(f"   Ищем: {desired_outcome}")
            for market in odds_markets:
                if market.get("market") == "one_x_two":
                    for outcome in market.get("outcomes", []):
                        if outcome.get("outcome") == desired_outcome:
                            print(f"   Найден коэффициент: {outcome.get('value')} от {outcome.get('bookmaker', {}).get('name', '?')}")
else:
    print("\nМатчи не прошли _select_top_matches")
    print("Возможные причины:")
    print("  - Нет коэффициентов (odds.value is None)")
    print("  - Коэффициент > 1.85 (PRIMARY_MAX_ODDS)")
    print("  - Коэффициент > 2.00 (EXTENDED_MAX_ODDS)")
    print("  - Недостаточное доминирование для extended tier")
    print("  - dominance_score <= 0")

# Проверяем дедупликацию
print("\n" + "=" * 60)
print("ПРОВЕРКА ДЕДУПЛИКАЦИИ:")
print("=" * 60)

recent_slugs = _get_recent_slugs(hours=4)
print(f"Недавно отправленные (за 4 часа): {len(recent_slugs)} матчей")

if top_matches:
    filtered = _filter_duplicates(top_matches, recent_slugs)
    print(f"После дедупликации: {len(filtered)} матчей")
    if len(filtered) < len(top_matches):
        print(f"Отфильтровано дубликатов: {len(top_matches) - len(filtered)}")
        for m in top_matches:
            slug = m.get("slug", "")
            if slug in recent_slugs:
                teams = m.get("teams", [])
                print(f"  Дубликат: {teams[0] if teams else '?'} - {teams[1] if len(teams) > 1 else '?'} ({slug})")

