#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Тест парсинга snapshot"""

# Тестовые данные из реального snapshot
test_snapshot = {
    "document": {
        "main": {
            "text": "20:00 Перерыв",
            "link": {
                "/url": "/ru/handball/m-16-11-2025-neka-tatabanya-carbonex"
            },
            "text2": "20:45 1-й т.",
            "link2": {
                "/url": "/ru/handball/m-12-11-2025-kolstad-handball-veszprem"
            },
            "text3": "20:00 2-й т.",
            "link3": {
                "/url": "/ru/handball/m-16-11-2025-ftc-w-vasas-w-"
            }
        }
    }
}

from scores24_snapshot_enricher import extract_minutes_from_snapshot

print("Тест парсинга минут из snapshot:")
minutes = extract_minutes_from_snapshot(test_snapshot, "handball")
print(f"Найдено минут: {len(minutes)}")
for slug, minute in minutes.items():
    print(f"  {slug}: {minute}")

