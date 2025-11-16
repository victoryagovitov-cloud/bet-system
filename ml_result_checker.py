# -*- coding: utf-8 -*-
"""
ML-РЕЗУЛЬТАТЫ: Проверка финальных счетов и обновление PredictionLoggerML
"""
from datetime import datetime
from prediction_logger_ml import PredictionLoggerML
from result_checker import ResultChecker


class MLResultChecker:
    def __init__(self):
        self.ml = PredictionLoggerML()
        self.rc = ResultChecker()

    def check_pending(self, min_age_minutes: int = 90):
        pending = [p for p in self.ml.predictions['predictions'] if p.get('status') == 'pending']
        if not pending:
            print("✅ Нет ML-прогнозов в статусе pending")
            return

        print(f"📋 ML pending: {len(pending)}")
        self.rc.setup_driver()
        try:
            for pred in pending:
                # Фильтр по возрасту
                try:
                    ts = datetime.fromisoformat(pred['timestamp'])
                except Exception:
                    ts = datetime.now()
                age = (datetime.now() - ts).total_seconds() / 60
                if age < min_age_minutes:
                    continue

                result = self.rc.check_match_result({
                    'sport': pred['sport'],
                    'team1': pred['team1'],
                    'team2': pred['team2'],
                })
                if result.get('status') in ('won', 'lost', 'cancelled') and result.get('final_score'):
                    self.ml.update_prediction_result_ml(pred['id'], result['final_score'],
                                                        'won' if result['status'] == 'won' else ('lost' if result['status'] == 'lost' else 'cancelled'))
        finally:
            self.rc.close_driver()


if __name__ == "__main__":
    checker = MLResultChecker()
    checker.check_pending(min_age_minutes=90)


