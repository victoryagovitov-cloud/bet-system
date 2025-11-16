# -*- coding: utf-8 -*-
"""
🔧 УЛУЧШЕННЫЙ КОННЕКТОР К SCORES24
- Увеличенное время ожидания
- Прокрутка страницы для подгрузки контента
- Поиск в конкретных элементах
- Отладочная информация
"""
import sys
import io
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def setup_driver_improved():
    """Улучшенная настройка драйвера"""
    print("🔧 Настройка улучшенного драйвера...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # User-agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Блокируем только тяжёлые ресурсы
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.media": 2,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        import os
        os.environ['WDM_SSL_VERIFY'] = '0'
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    except:
        service = Service("chromedriver.exe")
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(20)  # Увеличили до 20 сек
    
    print("✅ Драйвер готов\n")
    return driver

def get_name_variants_improved(name):
    """Улучшенная генерация вариантов"""
    variants = set()
    
    # Базовый вариант
    name_clean = name.strip().lower()
    variants.add(name_clean)
    
    # Без скобок
    no_brackets = re.sub(r'\([^)]*\)', '', name).strip().lower()
    if no_brackets:
        variants.add(no_brackets)
    
    # Для составных имён
    if '/' in name:
        parts = name.split('/')
        for part in parts:
            variants.add(part.strip().lower())
    
    # Без инициалов
    if '.' in name:
        without_dot = name.split('.')[0].strip().lower()
        variants.add(without_dot)
    
    # Отдельные слова
    words = name.split()
    for word in words:
        clean_word = word.strip().lower()
        if len(clean_word) > 2:  # Игнорируем короткие слова типа "А", "ФК"
            variants.add(clean_word)
    
    # Последние 2 слова (для длинных названий)
    if len(words) >= 2:
        last_two = ' '.join(words[-2:]).lower()
        variants.add(last_two)
    
    # Транслитерация
    translit_map = {
        'шапекоэнсе': ['chapecoense', 'chape', 'chapecoénse'],
        'операрио': ['operario', 'operário'],
        'цинциннати': ['cincinnati', 'fc cincinnati'],
        'коламбус': ['columbus', 'crew'],
        'крю': ['crew'],
        'насиональ': ['nacional'],
        'серро': ['cerro'],
        'портеньо': ['porteno', 'porteño'],
        'сан каэтано': ['sao caetano', 'são caetano', 'caetano'],
        'сорокаба': ['sorocaba'],
        'крисиума': ['criciuma', 'criciúma'],
        'жоинвиль': ['joinville']
    }
    
    for rus, eng_list in translit_map.items():
        if rus in name_clean:
            variants.update(eng_list)
    
    return list(variants)

def scroll_and_wait(driver):
    """Прокручиваем страницу для подгрузки контента"""
    try:
        # Прокручиваем вниз
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(1)
        
        # Прокручиваем в начало
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
    except:
        pass

def check_scores24_improved(driver, sport, team1, team2, match_data):
    """
    Улучшенная проверка на Scores24
    """
    urls = {
        'football': 'https://scores24.live/ru/soccer?matchesFilter=live',
        'tennis': 'https://scores24.live/ru/tennis?matchesFilter=live',
        'handball': 'https://scores24.live/ru/handball?matchesFilter=live'
    }
    
    print(f"🔍 Проверяю: {team1} - {team2}")
    print(f"   Спорт: {sport}")
    
    try:
        url = urls[sport]
        print(f"   📡 Загружаю: {url}")
        
        # Загружаем страницу
        driver.get(url)
        
        # Ждём загрузки контента (увеличено время)
        print(f"   ⏳ Ожидание загрузки...")
        time.sleep(5)  # Было 3, стало 5
        
        # Прокручиваем для подгрузки
        print(f"   📜 Прокрутка страницы...")
        scroll_and_wait(driver)
        
        # Получаем контент
        page_source = driver.page_source
        page_lower = page_source.lower()
        
        # Сохраняем для отладки
        debug_file = f"debug_scores24_{sport}.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(page_source)
        print(f"   💾 Сохранено в {debug_file}")
        
        # Генерируем варианты
        team1_variants = get_name_variants_improved(team1)
        team2_variants = get_name_variants_improved(team2)
        
        print(f"   🔍 Варианты команды 1 ({len(team1_variants)}): {team1_variants[:5]}")
        print(f"   🔍 Варианты команды 2 ({len(team2_variants)}): {team2_variants[:5]}")
        
        # Поиск
        found_variants_1 = [v for v in team1_variants if v in page_lower]
        found_variants_2 = [v for v in team2_variants if v in page_lower]
        
        if found_variants_1:
            print(f"   ✅ Найдено команды 1: {found_variants_1}")
        if found_variants_2:
            print(f"   ✅ Найдено команды 2: {found_variants_2}")
        
        if found_variants_1 or found_variants_2:
            found_team = team1 if found_variants_1 else team2
            found_variant = found_variants_1[0] if found_variants_1 else found_variants_2[0]
            
            print(f"   ✅ МАТЧ НАЙДЕН!")
            return {
                'verified': True,
                'source': 'Scores24.live',
                'details': f"Найдено: {found_team} (вариант: {found_variant})",
                'match': match_data,
                'found_variants': found_variants_1 + found_variants_2
            }
        else:
            print(f"   ❌ Матч не найден")
            print(f"   💡 Проверьте файл {debug_file} вручную")
            return {'verified': False}
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return {'verified': False}

# ===================== ТЕСТ =====================

def test_improved_connector():
    """Тест улучшенного коннектора"""
    print("\n" + "="*70)
    print("🔧 ТЕСТ УЛУЧШЕННОГО КОННЕКТОРА К SCORES24")
    print("="*70 + "\n")
    
    test_matches = [
        {
            'sport': 'football',
            'team1': 'Шапекоэнсе',
            'team2': 'Операрио ПР',
            'league': 'Бразилия. Серия B',
            'score': '2:0',
            'odds': 1.01
        },
        {
            'sport': 'football',
            'team1': 'ФК Цинциннати',
            'team2': 'Коламбус Крю',
            'league': 'США. MLS',
            'score': '0:0',
            'odds': 2.6
        },
        {
            'sport': 'football',
            'team1': 'Насиональ А',
            'team2': 'Серро Портеньо',
            'league': 'Парагвай',
            'score': '1:1',
            'odds': 6.75
        }
    ]
    
    driver = setup_driver_improved()
    verified = []
    
    try:
        for i, match in enumerate(test_matches, 1):
            print(f"\n{'='*70}")
            print(f"МАТЧ {i}/{len(test_matches)}")
            print(f"{'='*70}\n")
            
            result = check_scores24_improved(
                driver,
                match['sport'],
                match['team1'],
                match['team2'],
                match
            )
            
            if result['verified']:
                verified.append(result)
            
            print()
    
    finally:
        driver.quit()
        print("\n🔧 Драйвер закрыт\n")
    
    # Итоги
    print("="*70)
    print("📊 ИТОГИ ТЕСТА")
    print("="*70)
    print(f"Проверено: {len(test_matches)}")
    print(f"Найдено: {len(verified)}")
    print(f"Успешность: {len(verified)/len(test_matches)*100:.1f}%")
    
    if verified:
        print("\n✅ Найденные матчи:")
        for v in verified:
            m = v['match']
            print(f"   • {m['team1']} - {m['team2']}")
            print(f"     Детали: {v['details']}")
    
    print("\n💡 Проверьте debug файлы:")
    print("   • debug_scores24_football.html")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_improved_connector()

