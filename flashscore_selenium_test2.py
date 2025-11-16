# -*- coding: utf-8 -*-
"""
Тест доступа к Flashscore через Selenium - подход 2
"""
import time
import sys
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Исправляем кодировку для Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_flashscore_v2():
    """Проверка доступа к Flashscore KZ - альтернативный метод"""
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        print("Запуск браузера...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(15)
        
        print("Загрузка главной страницы...")
        driver.get('https://www.flashscorekz.com/')
        time.sleep(2)
        
        print(f"URL: {driver.current_url}")
        print(f"Заголовок: {driver.title}")
        
        # Получаем HTML и ищем данные напрямую
        page_source = driver.page_source
        
        # Проверяем наличие ключевых элементов
        if 'flashscore' in page_source.lower():
            print("УСПЕХ: Страница Flashscore загружена!")
            print(f"Размер HTML: {len(page_source)} символов")
            
            # Ищем упоминания live матчей в HTML
            if 'live' in page_source.lower():
                print("Найдены LIVE элементы в HTML")
            
            # Пробуем использовать JavaScript для получения данных
            try:
                print("\nПопытка выполнить JavaScript...")
                js_result = driver.execute_script("return document.body.innerText;")
                if js_result:
                    print(f"JavaScript работает! Получено {len(js_result)} символов текста")
                    if 'live' in js_result.lower():
                        print("В тексте страницы есть 'live'")
            except Exception as e:
                print(f"JavaScript error: {e}")
        
        else:
            print("ОШИБКА: Страница не похожа на Flashscore")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"ОШИБКА: {e}")
        return False

if __name__ == "__main__":
    test_flashscore_v2()

