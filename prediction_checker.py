# -*- coding: utf-8 -*-
"""
МОДУЛЬ ПРОВЕРКИ РЕЗУЛЬТАТОВ ПРОГНОЗОВ
Автоматически проверяет результаты матчей и обновляет статистику
"""
import json
import os
from datetime import datetime
from prediction_logger import PredictionLogger

class PredictionChecker:
    def __init__(self, db_path="predictions_db"):
        self.db_path = db_path
        self.logger = PredictionLogger(db_path)
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.today_path = os.path.join(db_path, self.today)
    
    def check_prediction_result(self, match_id, final_score):
        """
        Проверяет правильность прогноза
        
        match_id: ID матча
        final_score: '3:0' - финальный счет
        
        Returns: True/False - правильность прогноза
        """
        json_filename = os.path.join(self.today_path, f"{match_id}.json")
        
        if not os.path.exists(json_filename):
            print(f"❌ Прогноз не найден: {match_id}")
            return None
        
        with open(json_filename, 'r', encoding='utf-8') as f:
            prediction = json.load(f)
        
        recommendation = prediction['recommendation']
        
        # Разбираем финальный счет
        score_parts = final_score.split(':')
        team1_goals = int(score_parts[0])
        team2_goals = int(score_parts[1])
        
        # Проверяем правильность прогноза
        is_correct = False
        
        if recommendation == 'П1':
            is_correct = team1_goals > team2_goals
        elif recommendation == 'П2':
            is_correct = team2_goals > team1_goals
        elif recommendation == 'X':
            is_correct = team1_goals == team2_goals
        elif recommendation.startswith('ТБ'):
            # Тотал больше (например: "ТБ 50.5")
            total = float(recommendation.split()[1])
            actual_total = team1_goals + team2_goals
            is_correct = actual_total > total
        elif recommendation.startswith('ТМ'):
            # Тотал меньше (например: "ТМ 50.5")
            total = float(recommendation.split()[1])
            actual_total = team1_goals + team2_goals
            is_correct = actual_total < total
        
        # Обновляем результат в логе
        self.logger.update_prediction_result(match_id, final_score, is_correct)
        
        return is_correct
    
    def get_daily_statistics(self, date=None):
        """
        Возвращает статистику за день
        
        Returns: {
            'total': 10,
            'correct': 7,
            'incorrect': 2,
            'pending': 1,
            'accuracy': 77.78,
            'by_sport': {...},
            'by_category': {...}
        }
        """
        if date is None:
            date = self.today
        
        date_path = os.path.join(self.db_path, date)
        
        if not os.path.exists(date_path):
            return None
        
        stats = {
            'total': 0,
            'correct': 0,
            'incorrect': 0,
            'pending': 0,
            'accuracy': 0.0,
            'by_sport': {},
            'by_category': {},
            'predictions': []
        }
        
        # Читаем все прогнозы
        for filename in os.listdir(date_path):
            if filename.endswith('.json'):
                with open(os.path.join(date_path, filename), 'r', encoding='utf-8') as f:
                    prediction = json.load(f)
                
                stats['total'] += 1
                
                if prediction['prediction_correct'] is True:
                    stats['correct'] += 1
                elif prediction['prediction_correct'] is False:
                    stats['incorrect'] += 1
                else:
                    stats['pending'] += 1
                
                # Статистика по видам спорта
                sport = prediction['sport']
                if sport not in stats['by_sport']:
                    stats['by_sport'][sport] = {'total': 0, 'correct': 0, 'incorrect': 0}
                stats['by_sport'][sport]['total'] += 1
                if prediction['prediction_correct'] is True:
                    stats['by_sport'][sport]['correct'] += 1
                elif prediction['prediction_correct'] is False:
                    stats['by_sport'][sport]['incorrect'] += 1
                
                # Статистика по категориям
                category = prediction['category'].split()[0]  # МЕРТВЫЙ, ИДЕАЛЬНЫЙ и т.д.
                if category not in stats['by_category']:
                    stats['by_category'][category] = {'total': 0, 'correct': 0, 'incorrect': 0}
                stats['by_category'][category]['total'] += 1
                if prediction['prediction_correct'] is True:
                    stats['by_category'][category]['correct'] += 1
                elif prediction['prediction_correct'] is False:
                    stats['by_category'][category]['incorrect'] += 1
                
                stats['predictions'].append(prediction)
        
        # Рассчитываем процент точности
        if stats['correct'] + stats['incorrect'] > 0:
            stats['accuracy'] = round(
                (stats['correct'] / (stats['correct'] + stats['incorrect'])) * 100,
                2
            )
        
        return stats


# ПРИМЕР ИСПОЛЬЗОВАНИЯ
if __name__ == "__main__":
    checker = PredictionChecker()
    
    # Получаем статистику за сегодня
    stats = checker.get_daily_statistics()
    
    if stats:
        print("\n📊 СТАТИСТИКА ЗА СЕГОДНЯ:")
        print(f"Всего прогнозов: {stats['total']}")
        print(f"Правильных: {stats['correct']} ✅")
        print(f"Неправильных: {stats['incorrect']} ❌")
        print(f"Ожидают результата: {stats['pending']} ⏳")
        print(f"Точность: {stats['accuracy']}%")
        
        print("\n📈 ПО ВИДАМ СПОРТА:")
        for sport, data in stats['by_sport'].items():
            print(f"{sport}: {data['correct']}/{data['total']} ({round(data['correct']/data['total']*100, 1)}%)")
        
        print("\n⭐ ПО КАТЕГОРИЯМ:")
        for category, data in stats['by_category'].items():
            print(f"{category}: {data['correct']}/{data['total']} ({round(data['correct']/data['total']*100, 1)}%)")
    else:
        print("📭 Нет прогнозов за сегодня")

