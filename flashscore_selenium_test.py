"""
Тест доступа к Flashscore через Selenium
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_flashscore():
    """Проверка доступа к Flashscore KZ"""
    
    # Настройки Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Без GUI
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        print("Запуск браузера...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # Пробуем открыть главную страницу
        print("Загрузка https://www.flashscorekz.com/...")
        driver.get('https://www.flashscorekz.com/')
        
        print(f"Текущий URL: {driver.current_url}")
        print(f"Заголовок страницы: {driver.title}")
        
        # Ждем загрузки контента
        time.sleep(3)
        
        # Пробуем найти элементы
        try:
            # Ищем навигацию по спорту
            nav_elements = driver.find_elements(By.CLASS_NAME, 'menu__link')
            print(f"\nНайдено навигационных элементов: {len(nav_elements)}")
            
            # Пробуем перейти на футбол
            print("\nПереход на страницу футбола...")
            driver.get('https://www.flashscorekz.com/football/')
            time.sleep(3)
            
            print(f"URL футбола: {driver.current_url}")
            print(f"Заголовок: {driver.title}")
            
            # Ищем live матчи
            live_matches = driver.find_elements(By.CLASS_NAME, 'event__match')
            print(f"\nНайдено LIVE матчей: {len(live_matches)}")
            
            # Выводим первые 3 матча
            for i, match in enumerate(live_matches[:3], 1):
                try:
                    match_text = match.text
                    print(f"\nМатч {i}:")
                    print(match_text[:200])  # Первые 200 символов
                except Exception as e:
                    print(f"Ошибка при чтении матча {i}: {e}")
            
            print("\n✅ УСПЕХ! Flashscore доступен через Selenium!")
            
        except Exception as e:
            print(f"\n❌ Ошибка при поиске элементов: {e}")
            
            # Выводим HTML для диагностики
            print("\nHTML страницы (первые 500 символов):")
            print(driver.page_source[:500])
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        return False

if __name__ == "__main__":
    test_flashscore()

