#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from generate_live_report import _filter_duplicates, _get_recent_slugs

# Тестовые данные
test_matches = [
    {"slug": "13-11-2025-f-lechno-wasiutynski-n-cox", "sport": "tennis"},
    {"slug": "13-11-2025-new-match", "sport": "football"},
]

recent_slugs = _get_recent_slugs(hours=4)

print("Тестовые матчи:")
for m in test_matches:
    slug = m.get("slug", "").strip()
    in_slugs = slug in recent_slugs if slug else False
    print(f"  {slug}: в recent_slugs = {in_slugs}")

print(f"\nRecent slugs содержит: {len(recent_slugs)} slug")
print(f"  '13-11-2025-f-lechno-wasiutynski-n-cox' in recent_slugs: {'13-11-2025-f-lechno-wasiutynski-n-cox' in recent_slugs}")

filtered = _filter_duplicates(test_matches, recent_slugs)
print(f"\nПосле фильтрации: {len(filtered)} матчей")
for m in filtered:
    print(f"  {m.get('slug')}")

