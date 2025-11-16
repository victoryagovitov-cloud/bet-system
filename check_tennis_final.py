#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_tennis_analyzer import analyze_live_tennis_matches
from generate_live_report import _get_recent_slugs, _filter_duplicates, _select_top_tennis_matches

print("=" * 60)
print("ПРОВЕРКА ФИНАЛЬНОГО ОТБОРА ТЕННИСА")
print("=" * 60)

# Получаем все проанализированные матчи
analyzed = analyze_live_tennis_matches(limit=80)
print(f"\nПосле analyze_live_tennis_matches: {len(analyzed)} матчей")

if analyzed:
    print("\nДетали найденных матчей:")
    for i, m in enumerate(analyzed[:5]):
        teams = m.get("teams", [])
        print(f"\n{i+1}. {teams[0] if teams else '?'} - {teams[1] if len(teams) > 1 else '?'}")
        print(f"   Slug: {m.get('slug', '?')}")
        print(f"   Счет сетов: {m.get('sets_score', '?')}")
        print(f"   Текущие геймы: {m.get('current_games', '?')}")
        print(f"   Доминирование: {m.get('dominance_score', 0):.2f}")
        print(f"   Points diff: {m.get('points_diff', 0):.2f}")
        print(f"   Breaks diff: {m.get('breaks_diff', 0):.2f}")
        print(f"   Всего геймов: {m.get('total_games_played', 0)}")
else:
    print("\nМатчи не прошли analyze_live_tennis_matches")
    print("Возможные причины:")
    print("  - points_diff < 4 (если есть points_won)")
    print("  - breaks_diff < 0")
    print("  - dominance_score <= 0")
    print("  - total_games_played < 6 и нет выигранных сетов")
    print("  - Недостаточное преимущество в счете")

# Проверяем отбор топ-матчей
print("\n" + "=" * 60)
print("ПРОВЕРКА _select_top_tennis_matches:")
print("=" * 60)

top_matches = _select_top_tennis_matches(limit=5)
print(f"После _select_top_tennis_matches: {len(top_matches)} матчей")

if top_matches:
    print("\nДетали топ-матчей:")
    for i, m in enumerate(top_matches):
        teams = m.get("teams", [])
        odds = m.get("odds_info")
        odds_value = odds.value if odds else None
        print(f"\n{i+1}. {teams[0] if teams else '?'} - {teams[1] if len(teams) > 1 else '?'}")
        print(f"   Коэффициент: {odds_value}")
        print(f"   Доминирование: {m.get('dominance_score', 0):.2f}")
else:
    print("\nМатчи не прошли _select_top_tennis_matches")
    print("Возможные причины:")
    print("  - Нет коэффициентов (odds.value is None)")
    print("  - Коэффициент > 1.85 (PRIMARY_MAX_ODDS)")
    print("  - Коэффициент > 2.00 (EXTENDED_MAX_ODDS)")
    print("  - Недостаточное доминирование для extended tier")

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

