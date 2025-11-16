#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path

html_file = Path(r'c:\Users\Мария\.cursor\projects\d-cursor-Backtothestart-09-11-2025\agent-tools\59ee6148-770c-4028-87f9-d84aabd53b21.txt')

with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("HTML Анализ:")
print("=" * 80)
print(f"Размер: {len(content)} символов\n")

# Проверяем ключевые слова
keywords = ['live', 'match', 'score', 'team', 'fixture', 'football', 'bet', '1.0', '2.0']

for keyword in keywords:
    count = content.lower().count(keyword)
    if count > 0:
        print(f"✅ '{keyword}': {count} раз")

print("\n" + "=" * 80)
print("\n📋 Первые 3000 символов HTML:\n")
print(content[:3000])

