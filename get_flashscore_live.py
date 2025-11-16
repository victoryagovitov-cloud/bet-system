# -*- coding: utf-8 -*-
"""
Получение LIVE-статистики с Flashscore через Selenium
"""
import time
import sys
import io
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Исправляем кодировку для Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_live_matches_selenium():
    """Получить LIVE матчи с Flashscore через Selenium"""
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    results = {
        'football': [],
        'tennis': [],
        'handball': []
    }
    
    try:
        print("🚀 Запуск браузера...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(20)
        
        # ФУТБОЛ
        print("\n⚽ Получение футбольных матчей...")
        try:
            driver.get('https://www.flashscorekz.com/')
            time.sleep(3)
            
            # Извлекаем данные через JavaScript
            js_script = """
            var matches = [];
            var liveElements = document.querySelectorAll('[class*="event"][class*="live"]');
            
            liveElements.forEach(function(el) {
                var text = el.innerText || el.textContent;
                if (text && text.length > 10) {
                    matches.push(text.substring(0, 200));
                }
            });
            
            return matches;
            """
            
            live_data = driver.execute_script(js_script)
            
            if live_data:
                print(f"   Найдено LIVE элементов: {len(live_data)}")
                for i, match in enumerate(live_data[:5], 1):
                    print(f"   {i}. {match[:100]}...")
                    results['football'].append(match)
            else:
                print("   LIVE футбол не найден")
                
        except Exception as e:
            print(f"   ❌ Ошибка футбола: {e}")
        
        # Сохраняем результаты
        with open('flashscore_live_data.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Данные сохранены в flashscore_live_data.json")
        print(f"   Футбол: {len(results['football'])} матчей")
        print(f"   Теннис: {len(results['tennis'])} матчей")
        print(f"   Гандбол: {len(results['handball'])} матчей")
        
        driver.quit()
        return results
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return None

if __name__ == "__main__":
    get_live_matches_selenium()

