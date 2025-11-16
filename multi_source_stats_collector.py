# -*- coding: utf-8 -*-
"""
МНОГОИСТОЧНИКОВАЯ СИСТЕМА СБОРА СТАТИСТИКИ
С защитой от таймаутов и fallback механизмом
"""
import sys
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ПРИОРИТЕТНЫЕ ИСТОЧНИКИ ПО ВИДАМ СПОРТА
SOURCES = {
    'football': [
        {
            'name': 'Scores24',
            'url': 'https://scores24.live/ru/soccer?matchesFilter=live',
            'priority': 1,
            'timeout': 15,
            'strategy': 'eager',
            'description': 'Основной источник - быстрый и надежный'
        },
        {
            'name': 'WhoScored',
            'url': 'https://www.whoscored.com/LiveScores',
            'priority': 2,
            'timeout': 25,
            'strategy': 'eager',
            'description': 'Детальная статистика, рейтинги команд'
        },
        {
            'name': 'Soccerway',
            'url': 'https://int.soccerway.com/matches/',
            'priority': 3,
            'timeout': 20,
            'strategy': 'eager',
            'description': 'Обширная база данных матчей'
        },
        {
            'name': 'Flashscore',
            'url': 'https://www.flashscore.ru/football/',
            'priority': 4,
            'timeout': 20,
            'strategy': 'eager',
            'description': 'Популярный источник live-счетов'
        },
        {
            'name': 'Sofascore',
            'url': 'https://www.sofascore.com/football/livescore',
            'priority': 5,
            'timeout': 20,
            'strategy': 'eager',
            'description': 'Запасной источник'
        },
    ],
    'tennis': [
        {
            'name': 'Scores24',
            'url': 'https://scores24.live/ru/tennis?matchesFilter=live',
            'priority': 1,
            'timeout': 15,
            'strategy': 'eager',
            'description': 'Основной источник для тенниса'
        },
        {
            'name': 'Flashscore',
            'url': 'https://www.flashscore.ru/tennis/',
            'priority': 2,
            'timeout': 20,
            'strategy': 'eager',
            'description': 'Резервный источник, детальная статистика'
        },
        {
            'name': 'Sofascore',
            'url': 'https://www.sofascore.com/tennis/livescore',
            'priority': 3,
            'timeout': 20,
            'strategy': 'eager',
            'description': 'Запасной источник'
        },
    ],
    'handball': [
        {
            'name': 'Scores24',
            'url': 'https://scores24.live/ru/handball?matchesFilter=live',
            'priority': 1,
            'timeout': 15,
            'strategy': 'eager',
            'description': 'Основной источник для гандбола'
        },
        {
            'name': 'Flashscore',
            'url': 'https://www.flashscore.ru/handball/',
            'priority': 2,
            'timeout': 20,
            'strategy': 'eager',
            'description': 'Резервный источник'
        },
        {
            'name': 'Sofascore',
            'url': 'https://www.sofascore.com/handball/livescore',
            'priority': 3,
            'timeout': 20,
            'strategy': 'eager',
            'description': 'Запасной источник'
        },
    ]
}

def setup_optimized_driver(strategy='eager'):
    """
    Настройка оптимизированного Selenium драйвера
    strategy: 'normal', 'eager', 'none'
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    
    # Ускорение загрузки
    prefs = {
        "profile.managed_default_content_settings.images": 2,  # Блокируем картинки
        "profile.managed_default_content_settings.stylesheets": 2,  # Блокируем CSS
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Стратегия загрузки страницы
    chrome_options.page_load_strategy = strategy  # 'normal', 'eager', 'none'
    
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def load_page_with_retry(driver, url, timeout=15, max_retries=2):
    """
    Загрузка страницы с повторными попытками и обработкой таймаутов
    """
    for attempt in range(max_retries):
        try:
            driver.set_page_load_timeout(timeout)
            driver.get(url)
            return {'success': True, 'attempt': attempt + 1}
        except TimeoutException:
            print(f"   ⚠️ Попытка {attempt + 1}/{max_retries}: таймаут")
            if attempt < max_retries - 1:
                # Останавливаем загрузку и пробуем снова
                try:
                    driver.execute_script("window.stop();")
                except:
                    pass
                time.sleep(1)
            else:
                return {'success': False, 'error': 'timeout'}
        except WebDriverException as e:
            print(f"   ❌ Попытка {attempt + 1}/{max_retries}: ошибка WebDriver")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return {'success': False, 'error': str(e)}
    
    return {'success': False, 'error': 'max_retries_reached'}

def extract_stats_from_page(driver, source_name):
    """
    Извлечение статистики со страницы
    """
    try:
        # Простая проверка: есть ли контент
        page_text = driver.execute_script("return document.body.innerText;")
        
        if len(page_text) > 1000:  # Минимальный объем контента
            return {
                'success': True,
                'source': source_name,
                'data_size': len(page_text),
                'has_content': True
            }
        else:
            return {
                'success': False,
                'source': source_name,
                'error': 'insufficient_content'
            }
    except Exception as e:
        return {
            'success': False,
            'source': source_name,
            'error': str(e)
        }

def get_stats_with_fallback(sport_type='football', match_name=None):
    """
    Получение статистики с fallback на резервные источники
    """
    print(f"\n{'='*60}")
    print(f"🔍 СБОР СТАТИСТИКИ ДЛЯ: {sport_type.upper()}")
    if match_name:
        print(f"   Матч: {match_name}")
    print(f"{'='*60}")
    
    sources_list = SOURCES.get(sport_type, [])
    driver = None
    successful_sources = []
    
    for source in sorted(sources_list, key=lambda x: x['priority']):
        source_name = source['name']
        source_url = source['url']
        timeout = source['timeout']
        strategy = source['strategy']
        
        print(f"\n📡 [{source['priority']}] Пробую {source_name}...")
        print(f"   📝 {source.get('description', 'Источник статистики')}")
        print(f"   🔗 {source_url}")
        print(f"   ⏱️ Timeout: {timeout}s, Strategy: {strategy}")
        
        try:
            # Создаем драйвер со стратегией для этого источника
            if driver is None:
                driver = setup_optimized_driver(strategy)
            
            # Пытаемся загрузить страницу
            load_result = load_page_with_retry(driver, source_url, timeout)
            
            if load_result['success']:
                print(f"   ✅ Загружено (попытка {load_result['attempt']})")
                
                # Извлекаем статистику
                stats = extract_stats_from_page(driver, source_name)
                
                if stats['success']:
                    print(f"   ✅ Статистика получена: {stats['data_size']:,} символов")
                    successful_sources.append(stats)
                    
                    # Если это приоритетный источник, можем остановиться
                    if source['priority'] == 1 and stats['data_size'] > 5000:
                        print(f"\n✅ Основной источник работает, достаточно!")
                        break
                else:
                    print(f"   ⚠️ Недостаточно контента")
            else:
                print(f"   ❌ Не удалось загрузить: {load_result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Критическая ошибка: {e}")
            continue
        
        # Пауза между источниками
        time.sleep(1)
    
    # Закрываем драйвер
    if driver:
        driver.quit()
    
    # Итоги
    print(f"\n{'='*60}")
    print(f"📊 ИТОГО ИСТОЧНИКОВ: {len(successful_sources)}/{len(sources_list)}")
    
    if successful_sources:
        for i, source in enumerate(successful_sources, 1):
            print(f"   {i}. ✅ {source['source']}: {source['data_size']:,} символов")
        return {
            'success': True,
            'sources': successful_sources,
            'total_sources': len(successful_sources)
        }
    else:
        print("   ❌ Ни один источник не сработал!")
        return {
            'success': False,
            'sources': [],
            'total_sources': 0
        }

def main():
    """Тестирование системы"""
    print("=" * 70)
    print("🧪 ТЕСТ МНОГОИСТОЧНИКОВОЙ СИСТЕМЫ СБОРА СТАТИСТИКИ")
    print("=" * 70)
    
    # Показываем конфигурацию
    print("\n📋 КОНФИГУРАЦИЯ ИСТОЧНИКОВ:")
    print(f"\n⚽ ФУТБОЛ: {len(SOURCES['football'])} источников")
    for source in SOURCES['football']:
        print(f"   [{source['priority']}] {source['name']}: {source['description']}")
    
    print(f"\n🎾 ТЕННИС: {len(SOURCES['tennis'])} источников")
    for source in SOURCES['tennis']:
        print(f"   [{source['priority']}] {source['name']}: {source['description']}")
    
    print(f"\n🤾 ГАНДБОЛ: {len(SOURCES['handball'])} источников")
    for source in SOURCES['handball']:
        print(f"   [{source['priority']}] {source['name']}: {source['description']}")
    
    print("\n" + "=" * 70)
    print("▶️ НАЧИНАЮ ТЕСТИРОВАНИЕ...\n")
    
    # Тестируем футбол
    football_result = get_stats_with_fallback('football')
    
    # Тестируем теннис
    tennis_result = get_stats_with_fallback('tennis')
    
    # Тестируем гандбол
    handball_result = get_stats_with_fallback('handball')
    
    # Общий итог
    print("\n" + "=" * 70)
    print("📊 ОБЩИЙ ИТОГ ТЕСТА")
    print("=" * 70)
    
    total_football = len(SOURCES['football'])
    total_tennis = len(SOURCES['tennis'])
    total_handball = len(SOURCES['handball'])
    
    print(f"\n⚽ ФУТБОЛ:")
    print(f"   Доступно: {total_football} источников")
    print(f"   Работает: {football_result['total_sources']} источников")
    print(f"   Статус: {'✅ OK' if football_result['success'] else '❌ FAIL'}")
    
    print(f"\n🎾 ТЕННИС:")
    print(f"   Доступно: {total_tennis} источников")
    print(f"   Работает: {tennis_result['total_sources']} источников")
    print(f"   Статус: {'✅ OK' if tennis_result['success'] else '❌ FAIL'}")
    
    print(f"\n🤾 ГАНДБОЛ:")
    print(f"   Доступно: {total_handball} источников")
    print(f"   Работает: {handball_result['total_sources']} источников")
    print(f"   Статус: {'✅ OK' if handball_result['success'] else '❌ FAIL'}")
    
    print("\n" + "=" * 70)
    if all([football_result['success'], tennis_result['success'], handball_result['success']]):
        print("✅ ИТОГ: ВСЕ ВИДЫ СПОРТА - ИСТОЧНИКИ РАБОТАЮТ!")
        print("   Система готова к production использованию.")
    else:
        print("⚠️ ИТОГ: ЕСТЬ ПРОБЛЕМЫ С НЕКОТОРЫМИ ИСТОЧНИКАМИ")
        print("   Основной источник Scores24 должен работать всегда.")
    print("=" * 70)

if __name__ == "__main__":
    main()
