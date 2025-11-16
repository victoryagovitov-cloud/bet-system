#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from generate_live_report import _select_top_matches, _filter_duplicates, _get_recent_slugs

print("=" * 60)
print("ПРОВЕРКА ДЕДУПЛИКАЦИИ")
print("=" * 60)

matches = _select_top_matches(limit=5)
print(f"\nДо дедупликации: {len(matches)} матчей")
for m in matches:
    slug = m.get("slug", "?")
    teams = m.get("teams", ["?", "?"])
    print(f"  - {slug}")
    print(f"    {teams[0]} vs {teams[1]}")

recent_slugs = _get_recent_slugs(4)
print(f"\nНедавно отправленные (за 4 часа): {len(recent_slugs)} матчей")
for slug in list(recent_slugs)[:5]:
    print(f"  - {slug}")

filtered = _filter_duplicates(matches, recent_slugs)
print(f"\nПосле дедупликации: {len(filtered)} матчей")
for m in filtered:
    slug = m.get("slug", "?")
    teams = m.get("teams", ["?", "?"])
    print(f"  - {slug}: {teams[0]} vs {teams[1]}")

# Проверяем точное совпадение
if matches:
    current_slug = matches[0].get("slug", "")
    print(f"\nТекущий slug: '{current_slug}'")
    print(f"В списке отправленных: {current_slug in recent_slugs}")
    
    # Проверяем частичное совпадение
    for sent_slug in recent_slugs:
        if "west-ham" in current_slug.lower() and "west-ham" in sent_slug.lower():
            print(f"\n⚠️ ВОЗМОЖНОЕ СОВПАДЕНИЕ:")
            print(f"  Текущий: {current_slug}")
            print(f"  Отправлен: {sent_slug}")

