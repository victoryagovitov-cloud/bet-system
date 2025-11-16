# -*- coding: utf-8 -*-
"""
📝 ЛОГИРОВАНИЕ ПРОГНОЗОВ

Сохраняет каждый отправленный прогноз в JSON для последующей проверки
"""
import json
import os
from datetime import datetime

class PredictionLogger:
    def __init__(self, log_file='predictions_log.json'):
        self.log_file = log_file
        self.predictions = self._load_predictions()
    
    def _load_predictions(self):
        """Загружает существующие прогнозы"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'predictions': []}
        return {'predictions': []}
    
    def _save_predictions(self):
        """Сохраняет прогнозы в файл"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.predictions, f, ensure_ascii=False, indent=2)
    
    def add_prediction(self, sport, team1, team2, league, score, odds, category, timestamp=None):
        """
        Добавляет новый прогноз
        
        Args:
            sport: 'football', 'tennis', 'handball'
            team1: Название первой команды/игрока
            team2: Название второй команды/игрока
            league: Лига/турнир
            score: Текущий счет
            odds: Коэффициент
            category: 'dead', 'perfect', 'excellent', 'good'
            timestamp: Время прогноза (если None - текущее)
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        prediction = {
            'id': len(self.predictions['predictions']) + 1,
            'timestamp': timestamp,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'sport': sport,
            'team1': team1,
            'team2': team2,
            'league': league,
            'score_at_prediction': score,
            'odds': odds,
            'category': category,
            'recommendation': 'П1',  # Всегда рекомендуем первого
            'status': 'pending',  # pending, won, lost, cancelled
            'final_score': None,
            'checked_at': None,
            'profit': None  # Будет рассчитан после проверки
        }
        
        self.predictions['predictions'].append(prediction)
        self._save_predictions()
        
        print(f"✅ Прогноз #{prediction['id']} сохранен: {team1} vs {team2}")
        return prediction['id']
    
    def get_pending_predictions(self):
        """Возвращает прогнозы, ожидающие проверки"""
        return [p for p in self.predictions['predictions'] if p['status'] == 'pending']
    
    def get_today_predictions(self):
        """Возвращает прогнозы за сегодня"""
        today = datetime.now().strftime('%Y-%m-%d')
        return [p for p in self.predictions['predictions'] if p['date'] == today]
    
    def update_prediction_result(self, prediction_id, status, final_score, checked_at=None):
        """
        Обновляет результат прогноза
        
        Args:
            prediction_id: ID прогноза
            status: 'won', 'lost', 'cancelled'
            final_score: Финальный счет
            checked_at: Время проверки
        """
        if checked_at is None:
            checked_at = datetime.now().isoformat()
        
        for pred in self.predictions['predictions']:
            if pred['id'] == prediction_id:
                pred['status'] = status
                pred['final_score'] = final_score
                pred['checked_at'] = checked_at
                
                # Рассчитываем прибыль (для ставки 100₽)
                if status == 'won':
                    pred['profit'] = round((pred['odds'] - 1) * 100, 2)
                elif status == 'lost':
                    pred['profit'] = -100
                else:
                    pred['profit'] = 0
                
                self._save_predictions()
                print(f"✅ Прогноз #{prediction_id} обновлен: {status}")
                return True
        
        print(f"❌ Прогноз #{prediction_id} не найден")
        return False
    
    def get_statistics(self, date=None):
        """
        Получает статистику по прогнозам
        
        Args:
            date: Дата в формате 'YYYY-MM-DD' (если None - за сегодня)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        day_predictions = [p for p in self.predictions['predictions'] if p['date'] == date]
        
        if not day_predictions:
            return None
        
        total = len(day_predictions)
        won = len([p for p in day_predictions if p['status'] == 'won'])
        lost = len([p for p in day_predictions if p['status'] == 'lost'])
        pending = len([p for p in day_predictions if p['status'] == 'pending'])
        cancelled = len([p for p in day_predictions if p['status'] == 'cancelled'])
        
        total_profit = sum(p['profit'] for p in day_predictions if p['profit'] is not None)
        
        win_rate = (won / (won + lost) * 100) if (won + lost) > 0 else 0
        
        # Статистика по видам спорта
        by_sport = {}
        for sport in ['football', 'tennis', 'handball']:
            sport_preds = [p for p in day_predictions if p['sport'] == sport]
            if sport_preds:
                sport_won = len([p for p in sport_preds if p['status'] == 'won'])
                sport_total = len([p for p in sport_preds if p['status'] in ['won', 'lost']])
                by_sport[sport] = {
                    'total': len(sport_preds),
                    'won': sport_won,
                    'lost': len([p for p in sport_preds if p['status'] == 'lost']),
                    'win_rate': (sport_won / sport_total * 100) if sport_total > 0 else 0
                }
        
        # Статистика по категориям
        by_category = {}
        for category in ['dead', 'perfect', 'excellent', 'good']:
            cat_preds = [p for p in day_predictions if p['category'] == category]
            if cat_preds:
                cat_won = len([p for p in cat_preds if p['status'] == 'won'])
                cat_total = len([p for p in cat_preds if p['status'] in ['won', 'lost']])
                by_category[category] = {
                    'total': len(cat_preds),
                    'won': cat_won,
                    'lost': len([p for p in cat_preds if p['status'] == 'lost']),
                    'win_rate': (cat_won / cat_total * 100) if cat_total > 0 else 0
                }
        
        return {
            'date': date,
            'total': total,
            'won': won,
            'lost': lost,
            'pending': pending,
            'cancelled': cancelled,
            'win_rate': round(win_rate, 1),
            'total_profit': round(total_profit, 2),
            'avg_profit_per_bet': round(total_profit / total, 2) if total > 0 else 0,
            'by_sport': by_sport,
            'by_category': by_category,
            'predictions': day_predictions
        }


# Пример использования
if __name__ == "__main__":
    logger = PredictionLogger()
    
    # Добавляем тестовый прогноз
    pred_id = logger.add_prediction(
        sport='football',
        team1='Шапекоэнсе',
        team2='Операрио ПР',
        league='Бразилия. Серия B',
        score='2:0',
        odds=1.01,
        category='dead'
    )
    
    print(f"\n📊 Статистика за сегодня:")
    stats = logger.get_statistics()
    if stats:
        print(f"Всего прогнозов: {stats['total']}")
        print(f"Выиграно: {stats['won']}")
        print(f"Проиграно: {stats['lost']}")
        print(f"Ожидают проверки: {stats['pending']}")
