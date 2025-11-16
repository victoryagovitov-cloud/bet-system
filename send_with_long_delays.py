#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ОТПРАВКА С ДЛИННЫМИ ЗАДЕРЖКАМИ
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import pyautogui
import pyperclip
import time
from datetime import datetime, timezone, timedelta

CHAT_X = 1603
CHAT_Y = 1340
MOSCOW_TZ = timezone(timedelta(hours=3))

def get_moscow_time():
    return datetime.now(MOSCOW_TZ)

def send_test_message():
    try:
        current_time = get_moscow_time()
        
        print("="*70)
        print("TEST S DLINYMI ZADERZHKAMI")
        print("="*70)
        print(f"Koordinaty: ({CHAT_X}, {CHAT_Y})")
        print()
        
        request_text = f"""🎯 ТЕСТОВЫЙ ЗАПРОС НА АНАЛИЗ BETBOOM - {current_time.strftime('%H:%M')} МСК

Проверь актуальные матчи на BetBoom:
- Футбол: https://betboom.ru/sport/football?period=all&type=live
- Теннис: https://betboom.ru/sport/tennis?period=all&type=live  
- Гандбол: https://betboom.ru/sport/handball?period=all&type=live

Проведи анализ по системе (включая гандбольные тоталы!) и отправь результаты в канал @TrueLiveBet

Время запроса: {current_time.strftime('%d.%m.%Y %H:%M:%S')} МСК"""
        
        print("1. Kopiruyu tekst...")
        pyperclip.copy(request_text)
        time.sleep(1.0)
        
        print("2. Dvoinoy klik dlya fokusa...")
        pyautogui.click(CHAT_X, CHAT_Y)
        time.sleep(0.3)
        pyautogui.click(CHAT_X, CHAT_Y)
        time.sleep(1.5)
        
        print("3. Ochishchayu pole (Ctrl+A)...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        
        print("4. Vstavlyayu (Ctrl+V)...")
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(2.0)
        
        print("5. Otpravlyayu (Enter)...")
        pyautogui.press('enter')
        time.sleep(1.0)
        
        print()
        print("="*70)
        print("GOTOVO!")
        print("="*70)
        
    except Exception as e:
        print(f"OSHIBKA: {e}")

if __name__ == "__main__":
    print()
    print("Nachnu cherez 3 sekundy...")
    print("Ubedis' chto Cursor vidno!")
    print()
    time.sleep(3)
    send_test_message()

