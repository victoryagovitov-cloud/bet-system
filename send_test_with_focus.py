#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ТЕСТОВАЯ ОТПРАВКА С АКТИВАЦИЕЙ ОКНА
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import pyautogui
import pyperclip
import time
from datetime import datetime, timezone, timedelta

# КООРДИНАТЫ поля ввода Cursor Chat
CHAT_X = 1415
CHAT_Y = 1350

MOSCOW_TZ = timezone(timedelta(hours=3))

def get_moscow_time():
    return datetime.now(MOSCOW_TZ)

def send_test_message():
    try:
        current_time = get_moscow_time()
        
        print("="*70)
        print("TEST S AKTIVACIEJ OKNA CURSOR")
        print("="*70)
        print(f"Koordinaty: ({CHAT_X}, {CHAT_Y})")
        print()
        
        # Текст запроса
        request_text = f"""🎯 ТЕСТОВЫЙ ЗАПРОС НА АНАЛИЗ BETBOOM - {current_time.strftime('%H:%M')} МСК

Проверь актуальные матчи на BetBoom:
- Футбол: https://betboom.ru/sport/football?period=all&type=live
- Теннис: https://betboom.ru/sport/tennis?period=all&type=live  
- Гандбол: https://betboom.ru/sport/handball?period=all&type=live

Проведи анализ по системе (включая гандбольные тоталы!) и отправь результаты в канал @TrueLiveBet

Время запроса: {current_time.strftime('%d.%m.%Y %H:%M:%S')} МСК"""
        
        print("1. Kopiruyu tekst...")
        pyperclip.copy(request_text)
        time.sleep(0.3)
        
        print("2. Klikayu po koordinatam dlya aktivacii okna...")
        pyautogui.click(CHAT_X, CHAT_Y)
        time.sleep(0.5)
        
        print("3. Eshche raz klikayu dlya fokusa...")
        pyautogui.click(CHAT_X, CHAT_Y)
        time.sleep(0.5)
        
        print("4. Ochishchayu pole (Ctrl+A)...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        
        print("5. Vstavlyayu tekst (Ctrl+V)...")
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1.0)
        
        print("6. Otpravlyayu (Enter)...")
        pyautogui.press('enter')
        time.sleep(0.5)
        
        print()
        print("="*70)
        print("ZAPROS OTPRAVLEN!")
        print("="*70)
        print()
        print("Prover' chat - dolzhno byt' soobshchenie s zapros om na analiz!")
        print()
        
    except Exception as e:
        print()
        print(f"OSHIBKA: {e}")
        print()

if __name__ == "__main__":
    print()
    print("Nachnu otpravku cherez 3 sekundy...")
    print("Ubedis' chto okno Cursor vidno!")
    print()
    time.sleep(3)
    send_test_message()

