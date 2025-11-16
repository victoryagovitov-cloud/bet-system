#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ОТПРАВКА ЧЕРЕЗ ГОРЯЧУЮ КЛАВИШУ CURSOR
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import pyautogui
import pyperclip
import time
from datetime import datetime, timezone, timedelta

MOSCOW_TZ = timezone(timedelta(hours=3))

def get_moscow_time():
    return datetime.now(MOSCOW_TZ)

def send_test_message():
    try:
        current_time = get_moscow_time()
        
        print("="*70)
        print("TEST CHEREZ GORYACHUYU KLAVISHU")
        print("="*70)
        print()
        
        request_text = f"""🎯 ТЕСТОВЫЙ ЗАПРОС НА АНАЛИЗ BETBOOM - {current_time.strftime('%H:%M')} МСК

Проверь актуальные матчи на BetBoom:
- Футбол: https://betboom.ru/sport/football?period=all&type=live
- Теннис: https://betboom.ru/sport/tennis?period=all&type=live  
- Гандбол: https://betboom.ru/sport/handball?period=all&type=live

Проведи анализ по системе (включая гандбольные тоталы!) и отправь результаты в канал @TrueLiveBet

Время запроса: {current_time.strftime('%d.%m.%Y %H:%M:%S')} МСК"""
        
        print("1. Kopiruyu tekst v bufer...")
        pyperclip.copy(request_text)
        time.sleep(0.5)
        
        print("2. Aktiviruyu Cursor (Alt+Tab)...")
        pyautogui.hotkey('alt', 'tab')
        time.sleep(1.0)
        
        print("3. Otkryvayu chat (Cmd+L ili Ctrl+L)...")
        # Пробуем Ctrl+L (стандартная горячая клавиша для чата в VS Code / Cursor)
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.8)
        
        print("4. Vstavlyayu tekst (Ctrl+V)...")
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1.5)
        
        print("5. Otpravlyayu (Enter)...")
        pyautogui.press('enter')
        time.sleep(0.5)
        
        print()
        print("="*70)
        print("ZAPROS OTPRAVLEN!")
        print("="*70)
        print()
        print("Prover' chat - dolzhno byt' soobshchenie!")
        
    except Exception as e:
        print(f"OSHIBKA: {e}")

if __name__ == "__main__":
    print()
    print("Nachnu cherez 3 sekundy...")
    print("Ubedis' chto Cursor - aktivnoe okno!")
    print()
    time.sleep(3)
    send_test_message()
