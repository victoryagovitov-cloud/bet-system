# -*- coding: utf-8 -*-
"""
🔍 ПРОВЕРКА РЕЗУЛЬТАТОВ МАТЧЕЙ

Проверяет результаты завершенных матчей на Scores24
"""
from improved_scores24_connector import setup_driver_improved
from prediction_logger import PredictionLogger
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import time
import re

class ResultChecker:
    def __init__(self):
        self.logger = PredictionLogger()
        self.driver = None
    
    def setup_driver(self):
        """Инициализация драйвера"""
        if self.driver is None:
            self.driver = setup_driver_improved()
            print("✅ Драйвер инициализирован")
    
    def close_driver(self):
        """Закрытие драйвера"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("🔧 Драйвер закрыт")
    
    def check_match_result(self, prediction):
        """
        Проверяет результат конкретного матча
        
        Args:
            prediction: Словарь с данными прогноза
        
        Returns:
            dict: {'status': 'won'/'lost'/'cancelled', 'final_score': '3:0'}
        """
        sport = prediction['sport']
        team1 = prediction['team1']
        team2 = prediction['team2']
        
        sport_urls = {
            'football': 'https://scores24.live/ru/soccer?matchesFilter=finished',
            'tennis': 'https://scores24.live/ru/tennis?matchesFilter=finished',
            'handball': 'https://scores24.live/ru/handball?matchesFilter=finished'
        }
        
        if sport not in sport_urls:
            return {'status': 'cancelled', 'final_score': None}
        
        print(f"\n🔍 Проверяю: {team1} - {team2}")
        
        try:
            url = sport_urls[sport]
            self.driver.get(url)
            time.sleep(5)
            
            # Прокрутка
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            page_text = self.driver.page_source.lower()
            
            # Генерация вариантов названий
            team1_variants = self._generate_variants(team1)
            team2_variants = self._generate_variants(team2)
            
            # Поиск команд
            team1_found = any(v in page_text for v in team1_variants)
            team2_found = any(v in page_text for v in team2_variants)
            
            if not (team1_found and team2_found):
                print(f"   ❌ Матч не найден (может еще не завершился)")
                return {'status': 'pending', 'final_score': None}
            
            # Поиск финального счета
            # Ищем паттерны типа "3:0", "2:1" и т.д.
            score_pattern = r'(\d+)[:\s-]+(\d+)'
            scores = re.findall(score_pattern, page_text)
            
            if scores:
                # Берем первый найденный счет после упоминания команд
                final_score = f"{scores[0][0]}:{scores[0][1]}"
                score1, score2 = int(scores[0][0]), int(scores[0][1])
                
                print(f"   📊 Финальный счет: {final_score}")
                
                # Определяем результат (мы всегда ставим на П1)
                if score1 > score2:
                    print(f"   ✅ ВЫИГРАЛИ!")
                    return {'status': 'won', 'final_score': final_score}
                elif score1 < score2:
                    print(f"   ❌ ПРОИГРАЛИ")
                    return {'status': 'lost', 'final_score': final_score}
                else:
                    print(f"   ⚖️ НИЧЬЯ")
                    return {'status': 'lost', 'final_score': final_score}  # Ничья = проигрыш для П1
            else:
                print(f"   ⚠️ Не удалось определить счет")
                return {'status': 'pending', 'final_score': None}
        
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return {'status': 'pending', 'final_score': None}
    
    def _generate_variants(self, name):
        """Генерирует варианты названий команды/игрока"""
        variants = [name.lower()]
        words = name.split()
        
        if len(words) > 1:
            variants.append(words[-1].lower())
            variants.append(words[0].lower())
        
        # Транслитерация (базовая)
        translits = {
            'шапекоэнсе': ['chapecoense', 'chape'],
            'операрио': ['operario', 'operário'],
            'синнер': ['sinner'],
            'медведев': ['medvedev'],
        }
        
        name_lower = name.lower()
        for rus, eng_list in translits.items():
            if rus in name_lower:
                variants.extend(eng_list)
        
        return list(set(variants))
    
    def check_pending_predictions(self, min_age_minutes=90):
        """
        Проверяет все ожидающие прогнозы
        
        Args:
            min_age_minutes: Минимальный возраст прогноза для проверки (чтобы матч успел завершиться)
        """
        pending = self.logger.get_pending_predictions()
        
        if not pending:
            print("✅ Нет прогнозов, ожидающих проверки")
            return
        
        print(f"\n📋 Найдено {len(pending)} прогнозов для проверки\n")
        
        self.setup_driver()
        
        try:
            for pred in pending:
                # Проверяем возраст прогноза
                pred_time = datetime.fromisoformat(pred['timestamp'])
                age_minutes = (datetime.now() - pred_time).total_seconds() / 60
                
                if age_minutes < min_age_minutes:
                    print(f"⏳ Прогноз #{pred['id']} слишком свежий ({int(age_minutes)} мин), пропускаем")
                    continue
                
                result = self.check_match_result(pred)
                
                if result['status'] != 'pending':
                    self.logger.update_prediction_result(
                        pred['id'],
                        result['status'],
                        result['final_score']
                    )
        finally:
            self.close_driver()
    
    def check_today_predictions(self):
        """Проверяет все прогнозы за сегодня"""
        today_preds = self.logger.get_today_predictions()
        pending = [p for p in today_preds if p['status'] == 'pending']
        
        if not pending:
            print("✅ Все прогнозы за сегодня проверены")
            return
        
        print(f"\n📋 Проверяю {len(pending)} прогнозов за сегодня\n")
        
        self.setup_driver()
        
        try:
            for pred in pending:
                result = self.check_match_result(pred)
                
                if result['status'] != 'pending':
                    self.logger.update_prediction_result(
                        pred['id'],
                        result['status'],
                        result['final_score']
                    )
                
                time.sleep(2)  # Небольшая задержка между проверками
        finally:
            self.close_driver()


# Пример использования
if __name__ == "__main__":
    checker = ResultChecker()
    
    print("="*70)
    print("🔍 ПРОВЕРКА РЕЗУЛЬТАТОВ ПРОГНОЗОВ")
    print("="*70)
    
    # Проверяем прогнозы старше 90 минут
    checker.check_pending_predictions(min_age_minutes=90)
    
    print("\n" + "="*70)
    print("📊 СТАТИСТИКА ЗА СЕГОДНЯ")
    print("="*70)
    
    stats = checker.logger.get_statistics()
    if stats:
        print(f"\nВсего прогнозов: {stats['total']}")
        print(f"Выиграно: {stats['won']}")
        print(f"Проиграно: {stats['lost']}")
        print(f"Ожидают проверки: {stats['pending']}")
        print(f"Процент побед: {stats['win_rate']}%")
        print(f"Прибыль: {stats['total_profit']}₽")

