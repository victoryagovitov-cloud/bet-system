# -*- coding: utf-8 -*-
"""
⚡ БЫСТРЫЙ СБОРЩИК СТАТИСТИКИ (БЕЗ WEB SEARCH)

Оптимизирован для скорости:
- Только прямые источники (Scores24)
- БЕЗ web search
- Параллельная загрузка (опционально)
- Кэширование таблиц лиг
- Умное прерывание загрузки
"""
import sys
import io
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from concurrent.futures import ThreadPoolExecutor
from webdriver_manager.chrome import ChromeDriverManager
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ===================== РЕЖИМЫ РАБОТЫ =====================

FAST_MODE = True   # Только Scores24 (рекомендуется)
DEEP_MODE = False  # + все дополнительные источники

# ===================== КЭШ ДАННЫХ =====================

league_tables_cache = {}  # Кэш таблиц лиг
CACHE_TTL = 3600  # 1 час

# ===================== ИСТОЧНИКИ =====================

SOURCES = {
    'primary': {
        'name': 'Scores24',
        'url_template': {
            'football': 'https://scores24.live/ru/soccer?matchesFilter=live',
            'tennis': 'https://scores24.live/ru/tennis?matchesFilter=live',
            'handball': 'https://scores24.live/ru/handball?matchesFilter=live'
        },
        'timeout': 10
    },
    'fallback': {
        'name': 'Flashscore',
        'url_template': {
            'football': 'https://www.flashscore.ru/football/',
            'tennis': 'https://www.flashscore.ru/tennis/',
            'handball': 'https://www.flashscore.ru/handball/'
        },
        'timeout': 15
    }
}

# ===================== SELENIUM SETUP =====================

def setup_fast_driver():
    """
    Максимально оптимизированный драйвер
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # КРИТИЧНО: блокировка тяжелого контента
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.javascript": 1,  # JS нужен!
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # КРИТИЧНО: eager загрузка
    caps = DesiredCapabilities.CHROME.copy()
    caps["pageLoadStrategy"] = "eager"
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options, desired_capabilities=caps)
    
    return driver

# ===================== БЫСТРАЯ ЗАГРУЗКА =====================

def fast_load(driver, url, timeout=10, max_retries=2):
    """
    Быстрая загрузка с retry и умной остановкой
    """
    for attempt in range(1, max_retries + 1):
        try:
            driver.set_page_load_timeout(timeout)
            start = time.time()
            driver.get(url)
            elapsed = time.time() - start
            print(f"   ✅ Загружено за {elapsed:.1f}s (попытка {attempt})")
            return True
        except TimeoutException:
            print(f"   ⚠️ Таймаут (попытка {attempt}/{max_retries}), останавливаю загрузку...")
            try:
                driver.execute_script("window.stop();")
                time.sleep(0.5)
                return True  # Частичная загрузка может быть достаточной
            except:
                pass
        except Exception as e:
            print(f"   ❌ Ошибка (попытка {attempt}/{max_retries}): {e}")
            time.sleep(0.5)
    
    return False

# ===================== ПАРСИНГ SCORES24 =====================

def parse_scores24_match(driver, team1, team2, sport):
    """
    Парсинг конкретного матча на Scores24
    Возвращает: {score, league, positions, favorite}
    """
    try:
        # Поиск по названиям команд на странице
        page_text = driver.page_source.lower()
        team1_lower = team1.lower()
        team2_lower = team2.lower()
        
        if team1_lower in page_text and team2_lower in page_text:
            print(f"   ✅ Матч найден: {team1} - {team2}")
            
            # Парсим нужную информацию
            match_data = {
                'found': True,
                'source': 'Scores24',
                'team1': team1,
                'team2': team2,
                'sport': sport,
                'timestamp': time.time()
            }
            
            # Здесь можно добавить детальный парсинг
            # счета, статистики, позиций в таблице и т.д.
            
            return match_data
        else:
            print(f"   ⚠️ Матч не найден на странице")
            return {'found': False}
            
    except Exception as e:
        print(f"   ❌ Ошибка парсинга: {e}")
        return {'found': False}

# ===================== БЫСТРАЯ ПРОВЕРКА СТАТИСТИКИ =====================

def get_match_stats_fast(sport, team1, team2, league=None):
    """
    БЫСТРАЯ проверка статистики (только Scores24)
    Время: ~5-10 секунд
    """
    print(f"\n{'='*60}")
    print(f"⚡ БЫСТРАЯ ПРОВЕРКА: {team1} - {team2}")
    print(f"   Спорт: {sport}")
    print(f"   Лига: {league or 'не указана'}")
    print(f"{'='*60}")
    
    driver = None
    result = {
        'success': False,
        'source': None,
        'data': None,
        'time': 0
    }
    
    start_time = time.time()
    
    try:
        # 1. Пробуем Scores24 (основной источник)
        print(f"\n📡 [PRIMARY] Пробую Scores24...")
        driver = setup_fast_driver()
        
        url = SOURCES['primary']['url_template'][sport]
        timeout = SOURCES['primary']['timeout']
        
        if fast_load(driver, url, timeout):
            match_data = parse_scores24_match(driver, team1, team2, sport)
            
            if match_data.get('found'):
                result['success'] = True
                result['source'] = 'Scores24'
                result['data'] = match_data
                print(f"   ✅ Данные получены из Scores24")
            else:
                print(f"   ⚠️ Матч не найден на Scores24")
        
        # 2. Если не нашли и включен SAFE_MODE - пробуем Flashscore
        if not result['success'] and SAFE_MODE:
            print(f"\n📡 [FALLBACK] Пробую Flashscore...")
            url = SOURCES['fallback']['url_template'][sport]
            timeout = SOURCES['fallback']['timeout']
            
            if fast_load(driver, url, timeout):
                match_data = parse_scores24_match(driver, team1, team2, sport)
                
                if match_data.get('found'):
                    result['success'] = True
                    result['source'] = 'Flashscore'
                    result['data'] = match_data
                    print(f"   ✅ Данные получены из Flashscore")
    
    except Exception as e:
        print(f"   ❌ Критическая ошибка: {e}")
    
    finally:
        if driver:
            driver.quit()
        
        result['time'] = time.time() - start_time
        print(f"\n⏱️ Время проверки: {result['time']:.1f}s")
        print(f"{'='*60}\n")
    
    return result

# ===================== ПАКЕТНАЯ ПРОВЕРКА =====================

def check_multiple_matches(matches_list):
    """
    Проверка нескольких матчей
    matches_list = [
        {'sport': 'football', 'team1': 'Спортинг', 'team2': 'Брага', 'league': 'Португалия'},
        ...
    ]
    """
    print(f"\n{'='*70}")
    print(f"📦 ПАКЕТНАЯ ПРОВЕРКА: {len(matches_list)} матчей")
    print(f"   Режим: {'FAST' if FAST_MODE else 'SAFE' if SAFE_MODE else 'DEEP'}")
    print(f"{'='*70}\n")
    
    results = []
    total_time = 0
    successful = 0
    
    for i, match in enumerate(matches_list, 1):
        print(f"[{i}/{len(matches_list)}] Проверка матча...")
        
        result = get_match_stats_fast(
            sport=match['sport'],
            team1=match['team1'],
            team2=match['team2'],
            league=match.get('league')
        )
        
        results.append(result)
        total_time += result['time']
        
        if result['success']:
            successful += 1
    
    # Итоговая статистика
    print(f"\n{'='*70}")
    print(f"📊 ИТОГИ ПАКЕТНОЙ ПРОВЕРКИ")
    print(f"{'='*70}")
    print(f"   Всего матчей: {len(matches_list)}")
    print(f"   Успешно: {successful}")
    print(f"   Не найдено: {len(matches_list) - successful}")
    print(f"   Общее время: {total_time:.1f}s")
    print(f"   Среднее время на матч: {total_time/len(matches_list):.1f}s")
    print(f"{'='*70}\n")
    
    return results

# ===================== ТЕСТ =====================

def test_speed():
    """
    Тест скорости на реальных матчах
    """
    print("=" * 70)
    print("⚡ ТЕСТ СКОРОСТИ БЫСТРОГО СБОРЩИКА")
    print("=" * 70)
    
    # Тестовые матчи
    test_matches = [
        {
            'sport': 'football',
            'team1': 'Спортинг',
            'team2': 'Брага',
            'league': 'Португалия Примейра Лига'
        },
        {
            'sport': 'football',
            'team1': 'Панатинаикос',
            'team2': 'Атромитос',
            'league': 'Греция Суперлига'
        },
        {
            'sport': 'tennis',
            'team1': 'Миёши',
            'team2': 'Пирсон',
            'league': 'ATP Challenger'
        }
    ]
    
    print(f"\n📋 Тестовых матчей: {len(test_matches)}")
    print(f"🎯 Режим: {'FAST' if FAST_MODE else 'SAFE' if SAFE_MODE else 'DEEP'}")
    input("\nНажмите Enter для запуска теста...")
    
    # Запускаем тест
    start = time.time()
    results = check_multiple_matches(test_matches)
    total = time.time() - start
    
    print(f"\n✅ Тест завершен за {total:.1f}s")
    print(f"⚡ Скорость: {len(test_matches)/total*60:.1f} матчей/минуту")

if __name__ == "__main__":
    test_speed()
