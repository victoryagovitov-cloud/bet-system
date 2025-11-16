# -*- coding: utf-8 -*-
"""
АВТОМАТИЧЕСКАЯ ПРОВЕРКА РЕЗУЛЬТАТОВ МАТЧЕЙ
Использует Scores24/Flashscore для получения финальных счетов
"""
import sys
import io
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from prediction_checker import PredictionChecker
from prediction_logger import PredictionLogger

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class AutoResultChecker:
    def __init__(self):
        self.checker = PredictionChecker()
        self.logger = PredictionLogger()
        self.driver = None
    
    def setup_driver(self):
        """Настройка Selenium драйвера"""
        options = webdriver.ChromeOptions()
        options.page_load_strategy = 'eager'
        options.add_argument('--headless')  # Без GUI
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        
        # Блокируем изображения и CSS для скорости
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2
        }
        options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=options)
        return self.driver
    
    def get_match_result_from_url(self, match_url):
        """
        Получает финальный результат матча по URL
        
        Args:
            match_url: URL матча на Scores24 или Flashscore
        
        Returns:
            final_score: '3:0' или None если не найден
        """
        try:
            if not self.driver:
                self.setup_driver()
            
            print(f"🔍 Проверяем матч: {match_url}")
            
            self.driver.get(match_url)
            
            # Ждем загрузки счета
            wait = WebDriverWait(self.driver, 10)
            
            # Для Scores24
            if 'scores24.live' in match_url:
                try:
                    # Ищем финальный счет (может быть разная структура)
                    score_element = wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "detailScore"))
                    )
                    final_score = score_element.text.strip()
                    
                    # Проверяем что матч завершен
                    status_element = self.driver.find_element(By.CLASS_NAME, "status")
                    status = status_element.text.strip()
                    
                    if 'Закончен' in status or 'Finished' in status:
                        print(f"✅ Матч завершен. Счет: {final_score}")
                        return final_score
                    else:
                        print(f"⏳ Матч еще не завершен. Статус: {status}")
                        return None
                
                except Exception as e:
                    print(f"⚠️ Ошибка парсинга Scores24: {e}")
                    return None
            
            # Для Flashscore
            elif 'flashscore.ru' in match_url:
                try:
                    score_element = wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "detailScore__wrapper"))
                    )
                    final_score = score_element.text.strip()
                    
                    # Проверяем статус
                    status_elements = self.driver.find_elements(By.CLASS_NAME, "fixedHeaderDuel__detailStatus")
                    if status_elements:
                        status = status_elements[0].text.strip()
                        if 'Закончен' in status or 'Finished' in status:
                            print(f"✅ Матч завершен. Счет: {final_score}")
                            return final_score
                    
                    print(f"⏳ Матч еще не завершен")
                    return None
                
                except Exception as e:
                    print(f"⚠️ Ошибка парсинга Flashscore: {e}")
                    return None
        
        except TimeoutException:
            print(f"❌ Таймаут при загрузке страницы: {match_url}")
            return None
        
        except Exception as e:
            print(f"❌ Ошибка при проверке матча: {e}")
            return None
    
    def check_all_today_predictions(self):
        """
        Проверяет все прогнозы за сегодня
        """
        print("=" * 60)
        print("🔍 АВТОМАТИЧЕСКАЯ ПРОВЕРКА РЕЗУЛЬТАТОВ")
        print("=" * 60)
        
        # Получаем все прогнозы за сегодня
        today = datetime.now().strftime("%Y-%m-%d")
        today_path = os.path.join(self.logger.db_path, today, today_path)
        
        if not os.path.exists(today_path):
            print("📭 Нет прогнозов за сегодня")
            return
        
        predictions_to_check = []
        
        # Читаем все прогнозы
        for filename in os.listdir(today_path):
            if filename.endswith('.json'):
                filepath = os.path.join(today_path, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    prediction = json.load(f)
                
                # Проверяем только те, у которых еще нет результата
                if prediction.get('prediction_correct') is None:
                    predictions_to_check.append(prediction)
        
        print(f"\n📋 Найдено прогнозов для проверки: {len(predictions_to_check)}")
        
        if len(predictions_to_check) == 0:
            print("✅ Все прогнозы уже проверены!")
            return
        
        # Проверяем каждый прогноз
        checked_count = 0
        pending_count = 0
        
        for prediction in predictions_to_check:
            match_url = prediction.get('match_url')
            match_id = prediction.get('match_id')
            
            if not match_url:
                print(f"⚠️ Нет URL для матча: {match_id}")
                continue
            
            print(f"\n{'='*60}")
            print(f"📍 {prediction['team1']} - {prediction['team2']}")
            print(f"{'='*60}")
            
            # Получаем финальный результат
            final_score = self.get_match_result_from_url(match_url)
            
            if final_score:
                # Проверяем правильность прогноза
                is_correct = self.checker.check_prediction_result(match_id, final_score)
                
                if is_correct is not None:
                    result_emoji = "✅" if is_correct else "❌"
                    print(f"{result_emoji} Результат: {final_score} - прогноз {'ПРАВИЛЬНЫЙ' if is_correct else 'НЕПРАВИЛЬНЫЙ'}")
                    checked_count += 1
                else:
                    print(f"⚠️ Не удалось проверить прогноз")
                    pending_count += 1
            else:
                print(f"⏳ Матч еще не завершен или результат недоступен")
                pending_count += 1
        
        # Закрываем браузер
        if self.driver:
            self.driver.quit()
        
        print("\n" + "=" * 60)
        print("📊 ИТОГИ ПРОВЕРКИ:")
        print("=" * 60)
        print(f"✅ Проверено: {checked_count}")
        print(f"⏳ Ожидают: {pending_count}")
        print("=" * 60)
    
    def close(self):
        """Закрывает драйвер"""
        if self.driver:
            self.driver.quit()


# ИСПОЛЬЗОВАНИЕ
if __name__ == "__main__":
    auto_checker = AutoResultChecker()
    
    try:
        auto_checker.check_all_today_predictions()
    finally:
        auto_checker.close()
    
    print("\n✅ Автоматическая проверка завершена!")

