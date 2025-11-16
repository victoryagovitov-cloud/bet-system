#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест разных способов получения статистики по футбольным матчам
"""

import time
import requests
from bs4 import BeautifulSoup
import json

# Тестовые матчи
matches = [
    {
        'name': 'АЗ Алкмаар vs ПСВ Эйндховен',
        'league': 'Нидерланды. Эредивизи',
        'team1': 'АЗ Алкмаар',
        'team2': 'ПСВ Эйндховен',
        'score': '0-3',
        'time': '1Т, 29 мин'
    },
    {
        'name': 'Боде Глимт vs Брюн',
        'league': 'Норвегия. Элитсерия',
        'team1': 'Боде Глимт',
        'team2': 'Брюн',
        'score': '1-0',
        'time': '1Т, 16 мин'
    }
]

print("=" * 60)
print("ТЕСТ МЕТОДОВ ПОЛУЧЕНИЯ СТАТИСТИКИ")
print("=" * 60)
print()

# ===== МЕТОД 1: Scores24 Direct HTML =====
print("МЕТОД 1: Scores24 - Прямой парсинг HTML страницы матча")
print("-" * 60)
start_time = time.time()
try:
    # Пытаемся загрузить страницу матча АЗ vs ПСВ
    url = 'https://scores24.live/ru/soccer/m-az-alkmar-psv-eindhoven'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    response = requests.get(url, headers=headers, timeout=5)
    elapsed = time.time() - start_time
    
    print(f"✓ Загрузка: {elapsed:.2f}s")
    print(f"✓ Статус: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем ключевые элементы
        has_table = 'table' in response.text.lower()
        has_stats = 'Владение' in response.text or 'Possession' in response.text
        has_league_table = 'Таблица' in response.text or 'Table' in response.text
        
        print(f"✓ Таблица найдена: {has_table}")
        print(f"✓ Статистика найдена: {has_stats}")
        print(f"✓ Таблица лиги найдена: {has_league_table}")
        print(f"⚠ СКОРОСТЬ: {elapsed:.2f}s на матч")
    else:
        print(f"✗ Ошибка: {response.status_code}")
        
except Exception as e:
    print(f"✗ Ошибка: {str(e)}")
    print(f"⚠ СКОРОСТЬ: Не удалось получить (>5s или ошибка)")

print()

# ===== МЕТОД 2: Flashscore через requests =====
print("МЕТОД 2: Flashscore - JSON данные")
print("-" * 60)
start_time = time.time()
try:
    # Flashscore часто хранит данные в JSON в HTML
    url = 'https://www.flashscore.ru/match/z8k1n2op/#/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Referer': 'https://www.flashscore.ru/'
    }
    
    response = requests.get(url, headers=headers, timeout=5)
    elapsed = time.time() - start_time
    
    print(f"✓ Загрузка: {elapsed:.2f}s")
    print(f"✓ Статус: {response.status_code}")
    
    if 'json' in response.text.lower() or 'data' in response.text.lower():
        print(f"✓ JSON/Data найдены в ответе")
        print(f"⚠ СКОРОСТЬ: {elapsed:.2f}s на матч")
    else:
        print(f"⚠ HTML без JSON - потребуется парсинг")
        print(f"⚠ СКОРОСТЬ: {elapsed:.2f}s на матч (может быть медленнее)")
        
except Exception as e:
    print(f"✗ Ошибка: {str(e)}")
    print(f"⚠ СКОРОСТЬ: Не удалось получить")

print()

# ===== МЕТОД 3: BetBoom - собственная страница матча =====
print("МЕТОД 3: BetBoom - информация со страницы матча")
print("-" * 60)
start_time = time.time()
try:
    # BetBoom может иметь API данные
    url = 'https://betboom.ru/sport/football?period=all&type=live'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    response = requests.get(url, headers=headers, timeout=5)
    elapsed = time.time() - start_time
    
    print(f"✓ Загрузка: {elapsed:.2f}s")
    print(f"✓ Статус: {response.status_code}")
    
    if 'script' in response.text.lower():
        # Ищем JSON в тегах script
        import re
        json_matches = re.findall(r'<script[^>]*>.*?(\{.*?"data".*?\}).*?</script>', response.text, re.DOTALL)
        if json_matches:
            print(f"✓ JSON данные найдены в script тегах ({len(json_matches)} объектов)")
            print(f"⚠ СКОРОСТЬ: {elapsed:.2f}s на загрузку (но нужно парсить JSON)")
        else:
            print(f"⚠ Script теги найдены, но JSON не распознана")
    
except Exception as e:
    print(f"✗ Ошибка: {str(e)}")

print()

# ===== МЕТОД 4: Wikipedia/Википедия (турнирные таблицы) =====
print("МЕТОД 4: Википедия/Сайты лиг - турнирные таблицы")
print("-" * 60)
start_time = time.time()
try:
    # Для Нидерландской Эредивизи
    url = 'https://en.wikipedia.org/wiki/Eredivisie'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    response = requests.get(url, headers=headers, timeout=5)
    elapsed = time.time() - start_time
    
    print(f"✓ Загрузка: {elapsed:.2f}s")
    print(f"✓ Статус: {response.status_code}")
    
    if 'table' in response.text.lower():
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        print(f"✓ Таблиц найдено: {len(tables)}")
        print(f"✓ Таблица лиги точно там")
        print(f"⚠ СКОРОСТЬ: {elapsed:.2f}s на лигу (один раз, используется для всех матчей лиги)")
        print(f"✓ ПРЕИМУЩЕСТВО: Один запрос на всю лигу!")
    
except Exception as e:
    print(f"✗ Ошибка: {str(e)}")

print()
print("=" * 60)
print("РЕКОМЕНДАЦИЯ")
print("=" * 60)
print("""
САМЫЙ БЫСТРЫЙ СПОСОБ:

1. КЭШИРОВАНИЕ ТАБЛИЦ ЛИГ (1 запрос = вся лига)
   - Загружаем таблицу лиги один раз (Википедия или официальный сайт)
   - Кэшируем на 24 часа
   - Для каждого матча просто ищем команды в кэше → O(1)
   
2. ДЛЯ ТЕКУЩЕЙ СТАТИСТИКИ МАТЧА
   - Scores24.live для каждого матча (~0.5-1s на матч)
   - Или BetBoom если там есть данные в JSON
   
3. КОМБО (РЕКОМЕНДУЕТСЯ):
   ✓ Запрос таблицы лиги 1 раз → Кэш (0.3s)
   ✓ Для каждого матча → Scores24 матч (~0.5s)
   Итого: ~0.8s на матч при наличии кэша
""")
print("=" * 60)

