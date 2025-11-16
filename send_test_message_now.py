#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ТЕСТОВАЯ ОТПРАВКА СООБЩЕНИЯ В CURSOR CHAT
Отправляет тестовое сообщение прямо сейчас
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import pyautogui
import pyperclip
import time
from datetime import datetime, timezone, timedelta

# ПРОВЕРЕННЫЕ КООРДИНАТЫ поля ввода Cursor Chat
CHAT_X = 1603
CHAT_Y = 1340

# Московская временная зона
MOSCOW_TZ = timezone(timedelta(hours=3))

def get_moscow_time():
    """Получить текущее время в Москве"""
    return datetime.now(MOSCOW_TZ)

def send_test_message():
    """Отправить тестовое сообщение в Cursor Chat"""
    try:
        current_time = get_moscow_time()
        
        print("="*70)
        print("TESTOVAYA OTPRAVKA SOOBSCHENIYA V CURSOR CHAT")
        print("="*70)
        print(f"Vremya: {current_time.strftime('%H:%M:%S')} MSK")
        print(f"Koordinaty: ({CHAT_X}, {CHAT_Y})")
        print()
        print("Nachnu otpravku cherez 3 sekundy...")
        print("Ukazhite na pole vvoda chata!")
        print()
        
        time.sleep(3)
        
        # Текст тестового запроса
        request_text = f"""🎯 ТЕСТОВЫЙ ЗАПРОС НА АНАЛИЗ BETBOOM - {current_time.strftime('%H:%M')} МСК

Проверь актуальные матчи на BetBoom:
- Футбол: https://betboom.ru/sport/football?period=all&type=live
- Теннис: https://betboom.ru/sport/tennis?period=all&type=live  
- Гандбол: https://betboom.ru/sport/handball?period=all&type=live

Проведи анализ по системе (включая гандбольные тоталы!) и отправь результаты в канал @TrueLiveBet

Время запроса: {current_time.strftime('%d.%m.%Y %H:%M:%S')} МСК"""
        
        print("Kopiruyu tekst v bufer obmena...")
        pyperclip.copy(request_text)
        
        print(f"Klikayu po koordinatam ({CHAT_X}, {CHAT_Y})...")
        pyautogui.click(CHAT_X, CHAT_Y)
        time.sleep(0.5)
        
        print("Vstavlyayu tekst (Ctrl+V)...")
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        
        print("Otpravlyayu (Enter)...")
        pyautogui.press('enter')
        
        print()
        print("="*70)
        print("ZAPROS USPESHNO OTPRAVLEN!")
        print("="*70)
        print()
        print("Teper' II dolzhen poluchit' zapros i provesti analiz.")
        print("Rezul'taty budut otpravleny v @TrueLiveBet")
        print()
        
    except Exception as e:
        print()
        print("="*70)
        print(f"OSHIBKA: {e}")
        print("="*70)
        print()
        print("Prover'te:")
        print("1. Okno Cursor otkryto")
        print("2. Pole vvoda chata vidno")
        print("3. Koordinaty pravilnye")
        print()

if __name__ == "__main__":
    send_test_message()

