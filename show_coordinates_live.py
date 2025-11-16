#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПОКАЗ КООРДИНАТ В РЕАЛЬНОМ ВРЕМЕНИ
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import pyautogui
import time

print("="*70)
print("POKAZYVAYU KOORDINATY MYSHI V REALNOM VREMENI")
print("="*70)
print()
print("Navedi mysh' na pole vvoda chata i zapomnii koordinaty")
print("Nazhmi Ctrl+C dlya vyhoda")
print()
print("-"*70)

try:
    while True:
        x, y = pyautogui.position()
        position_str = f"X: {x:4d}  Y: {y:4d}"
        print(f"\r{position_str}", end='', flush=True)
        time.sleep(0.1)
except KeyboardInterrupt:
    print()
    print()
    print("="*70)
    print("Ostanovleno")
    print("="*70)

