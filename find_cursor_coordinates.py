#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ОПРЕДЕЛЕНИЕ КООРДИНАТ ПОЛЯ ВВОДА CURSOR CHAT
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import pyautogui
import time

print("="*70)
print("OPREDELENIE KOORDINAT POLYA VVODA CURSOR CHAT")
print("="*70)
print()
print("Cherez 5 sekund:")
print("1. Navedi mysh' na pole vvoda chata (gde ty pishesh' soobscheniya)")
print("2. Uderzhivaj mysh' na meste")
print("3. Skript avtomaticheski opredelit koordinaty")
print()

for i in range(5, 0, -1):
    print(f"Ostalos' {i} sekund...")
    time.sleep(1)

print()
print("OPREDELYAYU KOORDINATY...")
time.sleep(0.5)

x, y = pyautogui.position()

print()
print("="*70)
print("KOORDINATY NAJDENY!")
print("="*70)
print(f"X = {x}")
print(f"Y = {y}")
print()
print(f"Zapishi eti koordinaty v working_autoclicker.py:")
print(f"CHAT_X = {x}")
print(f"CHAT_Y = {y}")
print()
print("="*70)

