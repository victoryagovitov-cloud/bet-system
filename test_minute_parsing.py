#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Тест парсинга минут из текста"""

import re

def _parse_minute_from_text(text: str, sport: str):
    """Парсит минуту из текста"""
    if not text or not isinstance(text, str):
        return None
    
    text_lower = text.lower()
    
    # Гандбол: "1-й т." = 0-30 мин, "2-й т." = 30-60 мин, "Перерыв" = 30 мин
    if sport == "handball":
        if "перерыв" in text_lower:
            return 30
        elif "1-й т." in text_lower or "1-й тайм" in text_lower:
            # Первый тайм - примерно 15-25 минут (берем среднее 20)
            return 20
        elif "2-й т." in text_lower or "2-й тайм" in text_lower:
            # Второй тайм - примерно 35-50 минут (берем среднее 42)
            return 42
    
    return None

print("Тест парсинга минут:")
test_cases = [
    ("20:00 Перерыв", 30),
    ("20:45 1-й т.", 20),
    ("20:00 2-й т.", 42),
    ("18:30 1-й т.", 20),
    ("19:45 2-й т.", 42),
]

for text, expected in test_cases:
    result = _parse_minute_from_text(text, "handball")
    status = "OK" if result == expected else "FAIL"
    print(f"{status} '{text}' -> {result} (expected: {expected})")

