#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from generate_live_report import _get_recent_slugs, _select_top_tennis_matches
import csv
from pathlib import Path

print("=" * 70)
print("ПРОВЕРКА ДЕДУПЛИКАЦИИ")
print("=" * 70)

# Получаем недавние slugs
recent_slugs = _get_recent_slugs(hours=4)
print(f"\nНедавние slugs в окне дедупликации (последние 4 часа): {len(recent_slugs)}")
print("Последние 5:")
for i, slug in enumerate(list(recent_slugs)[-5:], 1):
    print(f"  {i}. {slug}")

# Получаем теннисные матчи
print("\n" + "=" * 70)
print("ТЕННИСНЫЕ МАТЧИ СЕЙЧАС:")
print("=" * 70)
tennis_matches = _select_top_tennis_matches(limit=10)
print(f"Найдено: {len(tennis_matches)} матчей")

for i, match in enumerate(tennis_matches[:5], 1):
    slug = match.get("slug", "").strip()
    teams = match.get("teams", [])
    home = teams[0] if teams else "?"
    away = teams[1] if len(teams) > 1 else "?"
    
    is_duplicate = slug in recent_slugs if slug else False
    status = "[DUPLICATE]" if is_duplicate else "[NEW]"
    
    print(f"\n{i}. {status} {home} vs {away}")
    print(f"   Slug: '{slug}'")
    print(f"   В recent_slugs: {slug in recent_slugs if slug else 'N/A'}")
    
    # Проверяем точное совпадение
    if slug:
        exact_match = any(s.strip() == slug for s in recent_slugs)
        print(f"   Точное совпадение: {exact_match}")

# Проверяем лог напрямую
print("\n" + "=" * 70)
print("ПРОВЕРКА ЛОГА НАПРЯМУЮ:")
print("=" * 70)
log_file = Path("data/recommendations_log.csv")
if log_file.exists():
    with log_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print(f"Всего записей в логе: {len(rows)}")
        
        # Ищем последние записи с этим slug
        target_slug = "13-11-2025-f-lechno-wasiutynski-n-cox"
        matching_rows = [r for r in rows if r.get("slug", "").strip() == target_slug]
        print(f"\nЗаписей с slug '{target_slug}': {len(matching_rows)}")
        
        if matching_rows:
            print("\nПоследние 3 записи:")
            for i, row in enumerate(matching_rows[-3:], 1):
                timestamp = row.get("timestamp_msk", "?")
                sport = row.get("sport", "?")
                print(f"  {i}. {timestamp} | {sport} | slug: {row.get('slug', '?')}")

