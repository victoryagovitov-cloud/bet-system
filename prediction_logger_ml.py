# -*- coding: utf-8 -*-
"""
🤖 ЛОГИРОВАНИЕ ПРОГНОЗОВ С ДАННЫМИ ДЛЯ МАШИННОГО ОБУЧЕНИЯ

Сохраняет полную статистику каждого прогноза для:
- Анализа паттернов
- Обучения ML моделей
- Улучшения системы
"""
import json
import os
from datetime import datetime

class PredictionLoggerML:
    """
    Улучшенный логгер с данными для ML
    """
    
    def __init__(self, log_file='predictions_ml_log.json'):
        self.log_file = log_file
        self.predictions = self._load_predictions()
    
    def _load_predictions(self):
        """Загружает существующие прогнозы"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'predictions': [], 'metadata': {'version': '2.0_ML'}}
        return {'predictions': [], 'metadata': {'version': '2.0_ML'}}
    
    def _save_predictions(self):
        """Сохраняет прогнозы в файл"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.predictions, f, ensure_ascii=False, indent=2)
    
    def add_prediction_ml(self, match_data, scores24_stats):
        """
        Добавляет прогноз с полными данными для ML
        
        Args:
            match_data: Базовые данные матча (команды, счет, коэфф)
            scores24_stats: Статистика со Scores24
        
        Returns:
            int: ID созданного прогноза
        """
        timestamp = datetime.now()
        
        # Извлекаем числовые показатели для ML
        ml_features = self._extract_ml_features(match_data, scores24_stats)
        
        prediction = {
            # Базовая информация
            'id': len(self.predictions['predictions']) + 1,
            'timestamp': timestamp.isoformat(),
            'date': timestamp.strftime('%Y-%m-%d'),
            'time': timestamp.strftime('%H:%M'),
            
            # Матч
            'sport': match_data.get('sport', 'football'),
            'team1': match_data.get('team1', ''),
            'team2': match_data.get('team2', ''),
            'league': match_data.get('league', ''),
            
            # Счет на момент прогноза
            'score_at_prediction': match_data.get('score', ''),
            'score_team1': ml_features.get('score_team1'),
            'score_team2': ml_features.get('score_team2'),
            'minute': ml_features.get('minute'),
            'half': ml_features.get('half'),
            
            # Коэффициент и категория
            'odds': match_data.get('odds', 999),
            'category': match_data.get('category', 'unknown'),
            'recommendation': 'П1',
            
            # ═══ ДАННЫЕ ДЛЯ ML ═══
            
            # Статистика матча (числовые)
            'ml_match_stats': {
                'xg_team1': ml_features.get('xg_team1'),
                'xg_team2': ml_features.get('xg_team2'),
                'xg_diff': ml_features.get('xg_diff'),
                'possession_team1': ml_features.get('possession_team1'),
                'possession_team2': ml_features.get('possession_team2'),
                'possession_diff': ml_features.get('possession_diff'),
                'shots_team1': ml_features.get('shots_team1'),
                'shots_team2': ml_features.get('shots_team2'),
                'shots_on_target_team1': ml_features.get('shots_on_target_team1'),
                'shots_on_target_team2': ml_features.get('shots_on_target_team2'),
                'corners_team1': ml_features.get('corners_team1'),
                'corners_team2': ml_features.get('corners_team2')
            },
            
            # H2H (числовые)
            'ml_h2h': {
                'team1_wins': ml_features.get('h2h_team1_wins'),
                'draws': ml_features.get('h2h_draws'),
                'team2_wins': ml_features.get('h2h_team2_wins'),
                'total_matches': ml_features.get('h2h_total'),
                'team1_win_rate': ml_features.get('h2h_team1_win_rate')
            },
            
            # Форма команд (числовые)
            'ml_form': {
                'team1_wins_last5': ml_features.get('form1_wins'),
                'team1_draws_last5': ml_features.get('form1_draws'),
                'team1_losses_last5': ml_features.get('form1_losses'),
                'team1_win_rate': ml_features.get('form1_win_rate'),
                'team2_wins_last5': ml_features.get('form2_wins'),
                'team2_draws_last5': ml_features.get('form2_draws'),
                'team2_losses_last5': ml_features.get('form2_losses'),
                'team2_win_rate': ml_features.get('form2_win_rate')
            },
            
            # Контекст
            'ml_context': {
                'is_late_match': ml_features.get('minute', 0) >= 80,  # 80+ минута
                'score_diff': ml_features.get('score_diff'),
                'is_dominant': ml_features.get('is_dominant'),  # xG diff > 1.0
                'odds_category_numeric': self._odds_to_numeric(match_data.get('odds', 999))
            },
            
            # Результат (заполняется после проверки)
            'status': 'pending',
            'final_score': None,
            'final_score_team1': None,
            'final_score_team2': None,
            'checked_at': None,
            'profit': None,
            
            # Сырые данные (для справки)
            'raw_scores24_stats': scores24_stats
        }
        
        self.predictions['predictions'].append(prediction)
        self._save_predictions()
        
        print(f"✅ ML-прогноз #{prediction['id']} сохранен: {match_data.get('team1')} vs {match_data.get('team2')}")
        return prediction['id']
    
    def _extract_ml_features(self, match_data, scores24_stats):
        """
        Извлекает числовые признаки для ML
        """
        features = {}
        
        # Парсим счет
        score = match_data.get('score', '0:0')
        try:
            parts = score.split(':')
            features['score_team1'] = int(parts[0].strip())
            features['score_team2'] = int(parts[1].split()[0].strip() if len(parts) > 1 else 0)
            features['score_diff'] = features['score_team1'] - features['score_team2']
        except:
            features['score_team1'] = 0
            features['score_team2'] = 0
            features['score_diff'] = 0
        
        # Минута матча
        time_str = match_data.get('time', '')
        features['minute'] = self._parse_minute(time_str)
        features['half'] = 1 if features['minute'] <= 45 else 2
        
        # Статистика матча
        match_stats = scores24_stats.get('match_stats', {})
        
        if match_stats.get('xg'):
            xg = match_stats['xg']
            if isinstance(xg, dict):
                features['xg_team1'] = xg.get('team1', 0)
                features['xg_team2'] = xg.get('team2', 0)
            elif isinstance(xg, str):
                try:
                    parts = xg.split('-')
                    features['xg_team1'] = float(parts[0].strip())
                    features['xg_team2'] = float(parts[1].strip())
                except:
                    features['xg_team1'] = 0
                    features['xg_team2'] = 0
            
            features['xg_diff'] = features.get('xg_team1', 0) - features.get('xg_team2', 0)
            features['is_dominant'] = features['xg_diff'] > 1.0
        
        if match_stats.get('possession'):
            poss = match_stats['possession']
            if isinstance(poss, dict):
                features['possession_team1'] = poss.get('team1', 50)
                features['possession_team2'] = poss.get('team2', 50)
            elif isinstance(poss, str):
                try:
                    parts = poss.replace('%', '').split('-')
                    features['possession_team1'] = int(parts[0].strip())
                    features['possession_team2'] = int(parts[1].strip())
                except:
                    features['possession_team1'] = 50
                    features['possession_team2'] = 50
            
            features['possession_diff'] = features.get('possession_team1', 50) - features.get('possession_team2', 50)
        
        if match_stats.get('shots'):
            shots = match_stats['shots']
            if isinstance(shots, str):
                try:
                    parts = shots.split('-')
                    features['shots_team1'] = int(parts[0].strip())
                    features['shots_team2'] = int(parts[1].strip())
                except:
                    pass
        
        if match_stats.get('shots_on_target'):
            sot = match_stats['shots_on_target']
            if isinstance(sot, str):
                try:
                    parts = sot.split('-')
                    features['shots_on_target_team1'] = int(parts[0].strip())
                    features['shots_on_target_team2'] = int(parts[1].strip())
                except:
                    pass
        
        if match_stats.get('corners'):
            corners = match_stats['corners']
            if isinstance(corners, str):
                try:
                    parts = corners.split('-')
                    features['corners_team1'] = int(parts[0].strip())
                    features['corners_team2'] = int(parts[1].strip())
                except:
                    pass
        
        # H2H
        h2h = scores24_stats.get('h2h')
        if h2h:
            if isinstance(h2h, dict):
                features['h2h_team1_wins'] = h2h.get('team1_wins', 0)
                features['h2h_draws'] = h2h.get('draws', 0)
                features['h2h_team2_wins'] = h2h.get('team2_wins', 0)
            elif isinstance(h2h, str):
                try:
                    parts = h2h.split('-')
                    features['h2h_team1_wins'] = int(parts[0])
                    features['h2h_draws'] = int(parts[1])
                    features['h2h_team2_wins'] = int(parts[2])
                except:
                    pass
            
            total_h2h = features.get('h2h_team1_wins', 0) + features.get('h2h_draws', 0) + features.get('h2h_team2_wins', 0)
            features['h2h_total'] = total_h2h
            features['h2h_team1_win_rate'] = (features.get('h2h_team1_wins', 0) / total_h2h * 100) if total_h2h > 0 else 0
        
        # Форма
        form = scores24_stats.get('form', {})
        if form:
            team1_form = form.get('team1', {})
            team2_form = form.get('team2', {})
            
            features['form1_wins'] = team1_form.get('wins', 0)
            features['form1_draws'] = team1_form.get('draws', 0)
            features['form1_losses'] = team1_form.get('losses', 0)
            features['form1_win_rate'] = (features['form1_wins'] / 5 * 100) if features.get('form1_wins') else 0
            
            features['form2_wins'] = team2_form.get('wins', 0)
            features['form2_draws'] = team2_form.get('draws', 0)
            features['form2_losses'] = team2_form.get('losses', 0)
            features['form2_win_rate'] = (features['form2_wins'] / 5 * 100) if features.get('form2_wins') else 0
        
        return features
    
    def _parse_minute(self, time_str):
        """Парсит минуту из строки типа '2Т, 71 мин' или '85'"""
        try:
            import re
            # Ищем число перед "мин" или просто число
            match = re.search(r'(\d+)', time_str)
            if match:
                minute = int(match.group(1))
                # Если указан 2-й тайм, добавляем 45
                if '2' in time_str or 'Т' in time_str:
                    if minute < 50:  # Если уже не добавлено
                        minute += 45
                return minute
        except:
            pass
        return 0
    
    def _odds_to_numeric(self, odds):
        """Преобразует категорию odds в числовое значение для ML"""
        if odds <= 1.05:
            return 5  # МЕРТВЫЙ
        elif odds <= 1.20:
            return 4  # ИДЕАЛЬНЫЙ
        elif odds <= 1.50:
            return 3  # ОТЛИЧНЫЙ
        elif odds <= 2.50:
            return 2  # ХОРОШИЙ
        else:
            return 1  # СОМНИТЕЛЬНЫЙ
    
    def update_prediction_result_ml(self, prediction_id, final_score, status=None):
        """
        Обновляет результат прогноза с ML данными
        
        Args:
            prediction_id: ID прогноза
            final_score: Финальный счет (строка "2:1")
            status: 'won', 'lost' или None (определится автоматически)
        """
        for pred in self.predictions['predictions']:
            if pred['id'] == prediction_id:
                # Парсим финальный счет
                try:
                    parts = final_score.split(':')
                    final_team1 = int(parts[0].strip())
                    final_team2 = int(parts[1].strip())
                except:
                    print(f"❌ Не удалось распарсить финальный счет: {final_score}")
                    return False
                
                # Определяем результат
                if status is None:
                    # Автоматически определяем по финальному счету
                    if final_team1 > final_team2:
                        status = 'won'
                    elif final_team1 < final_team2:
                        status = 'lost'
                    else:
                        status = 'cancelled'  # Ничья - не угадали
                
                # Обновляем
                pred['final_score'] = final_score
                pred['final_score_team1'] = final_team1
                pred['final_score_team2'] = final_team2
                pred['status'] = status
                pred['checked_at'] = datetime.now().isoformat()
                
                # Рассчитываем прибыль
                if status == 'won':
                    pred['profit'] = round((pred['odds'] - 1) * 100, 2)
                elif status == 'lost':
                    pred['profit'] = -100
                else:
                    pred['profit'] = 0
                
                # ML метрики
                pred['ml_result'] = {
                    'predicted_correctly': status == 'won',
                    'score_changed': final_team1 != pred.get('score_team1', 0) or final_team2 != pred.get('score_team2', 0),
                    'goals_conceded': final_team2 - pred.get('score_team2', 0),
                    'goals_scored': final_team1 - pred.get('score_team1', 0)
                }
                
                self._save_predictions()
                print(f"✅ ML-прогноз #{prediction_id} обновлен: {status} ({final_score})")
                return True
        
        print(f"❌ Прогноз #{prediction_id} не найден")
        return False
    
    def get_ml_dataset(self):
        """
        Возвращает данные в формате для ML (pandas DataFrame compatible)
        
        Returns:
            list: Список словарей с числовыми признаками
        """
        ml_data = []
        
        for pred in self.predictions['predictions']:
            # Пропускаем прогнозы без результата
            if pred['status'] == 'pending':
                continue
            
            # Формируем строку для ML
            row = {
                # Target (то что предсказываем)
                'won': 1 if pred['status'] == 'won' else 0,
                
                # Features (признаки)
                'odds': pred['odds'],
                'odds_category': pred['ml_context']['odds_category_numeric'] if 'ml_context' in pred else self._odds_to_numeric(pred['odds']),
                'score_diff': pred.get('score_team1', 0) - pred.get('score_team2', 0),
                'minute': pred.get('minute', 0),
                'is_late_match': pred.get('minute', 0) >= 80,
                
                # Статистика
                'xg_team1': pred.get('ml_match_stats', {}).get('xg_team1', 0),
                'xg_team2': pred.get('ml_match_stats', {}).get('xg_team2', 0),
                'xg_diff': pred.get('ml_match_stats', {}).get('xg_diff', 0),
                'possession_team1': pred.get('ml_match_stats', {}).get('possession_team1', 50),
                'possession_diff': pred.get('ml_match_stats', {}).get('possession_diff', 0),
                'shots_team1': pred.get('ml_match_stats', {}).get('shots_team1', 0),
                'shots_team2': pred.get('ml_match_stats', {}).get('shots_team2', 0),
                'shots_on_target_team1': pred.get('ml_match_stats', {}).get('shots_on_target_team1', 0),
                'corners_team1': pred.get('ml_match_stats', {}).get('corners_team1', 0),
                
                # H2H
                'h2h_team1_wins': pred.get('ml_h2h', {}).get('team1_wins', 0),
                'h2h_draws': pred.get('ml_h2h', {}).get('draws', 0),
                'h2h_team2_wins': pred.get('ml_h2h', {}).get('team2_wins', 0),
                'h2h_team1_win_rate': pred.get('ml_h2h', {}).get('team1_win_rate', 0),
                
                # Форма
                'form1_wins': pred.get('ml_form', {}).get('team1_wins_last5', 0),
                'form1_win_rate': pred.get('ml_form', {}).get('team1_win_rate', 0),
                'form2_wins': pred.get('ml_form', {}).get('team2_wins_last5', 0),
                
                # Метаданные
                'sport': pred['sport'],
                'category': pred['category'],
                'date': pred['date']
            }
            
            ml_data.append(row)
        
        return ml_data
    
    def export_for_ml(self, output_file='ml_dataset.json'):
        """
        Экспортирует данные в формат для ML
        """
        ml_data = self.get_ml_dataset()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ml_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ ML dataset экспортирован: {output_file}")
        print(f"   Записей: {len(ml_data)}")
        return output_file
    
    def get_statistics(self, date=None):
        """
        Получает статистику (совместимо со старым логгером)
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
        
        total_profit = sum(p.get('profit', 0) for p in day_predictions if p.get('profit') is not None)
        win_rate = (won / (won + lost) * 100) if (won + lost) > 0 else 0
        
        return {
            'date': date,
            'total': total,
            'won': won,
            'lost': lost,
            'pending': pending,
            'win_rate': round(win_rate, 1),
            'total_profit': round(total_profit, 2),
            'predictions': day_predictions
        }


# ═══ ПРИМЕР ИСПОЛЬЗОВАНИЯ ═══

if __name__ == "__main__":
    print("="*70)
    print("🤖 ТЕСТ ML ЛОГГЕРА")
    print("="*70 + "\n")
    
    logger = PredictionLoggerML()
    
    # Пример данных матча
    match_data = {
        'sport': 'football',
        'team1': 'Спортинг',
        'team2': 'Алверка',
        'league': 'Португалия. Кубок лиги',
        'score': '2:0',
        'time': '2Т, 55 мин',
        'odds': 1.01,
        'category': 'dead'
    }
    
    # Пример статистики со Scores24
    scores24_stats = {
        'match_stats': {
            'xg': {'team1': 1.24, 'team2': 0.15},
            'possession': {'team1': 62, 'team2': 38},
            'shots': '4 - 2',
            'shots_on_target': '3 - 1',
            'corners': '2 - 1'
        },
        'h2h': {'team1_wins': 0, 'draws': 0, 'team2_wins': 1},
        'form': {
            'team1': {'wins': 3, 'draws': 1, 'losses': 1},
            'team2': {'wins': 2, 'draws': 1, 'losses': 2}
        }
    }
    
    # Сохраняем прогноз
    pred_id = logger.add_prediction_ml(match_data, scores24_stats)
    
    print(f"\n📊 Прогноз создан с ID: {pred_id}")
    print("\n💾 Сохраненные ML признаки:")
    
    pred = logger.predictions['predictions'][-1]
    print(f"\n   Статистика матча:")
    for key, value in pred['ml_match_stats'].items():
        if value is not None:
            print(f"      {key}: {value}")
    
    print(f"\n   H2H:")
    for key, value in pred['ml_h2h'].items():
        print(f"      {key}: {value}")
    
    print(f"\n   Форма:")
    for key, value in pred['ml_form'].items():
        print(f"      {key}: {value}")
    
    # Экспорт для ML
    print("\n" + "="*70)
    print("📤 ЭКСПОРТ ДЛЯ ML")
    print("="*70 + "\n")
    
    logger.export_for_ml('test_ml_dataset.json')
    
    print("\n✅ Тест завершен!")

