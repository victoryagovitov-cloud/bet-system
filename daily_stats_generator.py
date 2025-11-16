# -*- coding: utf-8 -*-
"""
ГЕНЕРАТОР ДНЕВНОЙ СТАТИСТИКИ И ИНФОГРАФИКИ

Создает красивый отчет о результатах за день
"""
import sys
import io
# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from prediction_logger import PredictionLogger
from datetime import datetime
import json

class DailyStatsGenerator:
    def __init__(self):
        self.logger = PredictionLogger()
        self.disclaimers = [
            "Наши ставки, хоть и хороши, не являются инвестиционной рекомендацией. Ставьте с умом.",
            "Помните: даже лучшие прогнозы - это не гарантия. Играйте ответственно.",
            "Ставки - это риск. Наш анализ не финансовый совет. Принимайте решения осознанно.",
            "Мы делаем качественный анализ, но решение всегда за вами. Ставьте разумно.",
            "Прогнозы основаны на статистике, но спорт непредсказуем. Играйте с умом.",
        ]
    
    def _generate_progress_bar(self, percentage, length=10):
        """Генерирует текстовый прогресс-бар"""
        filled = int(percentage / 10)  # 10% на каждый блок
        empty = length - filled
        return '█' * filled + '░' * empty
    
    def _get_random_disclaimer(self):
        """Возвращает случайный дисклеймер"""
        import random
        return random.choice(self.disclaimers)
    
    def generate_text_infographic(self, stats):
        """
        Генерирует текстовую инфографику для Telegram
        
        Args:
            stats: Статистика из PredictionLogger.get_statistics()
        """
        if not stats:
            return "❌ Нет данных за этот день"
        
        date_obj = datetime.strptime(stats['date'], '%Y-%m-%d')
        date_formatted = date_obj.strftime('%d.%m.%Y')
        
        # Эмодзи для процента побед
        if stats['win_rate'] >= 90:
            rate_emoji = "🔥🔥🔥"
        elif stats['win_rate'] >= 75:
            rate_emoji = "🔥🔥"
        elif stats['win_rate'] >= 60:
            rate_emoji = "🔥"
        else:
            rate_emoji = "📊"
        
        # Генерируем прогресс-бар для общей результативности
        wins_bar = self._generate_progress_bar(stats['win_rate'])
        
        message = f"""═══════════════════════════════════
📊 ИТОГИ ДНЯ: {date_formatted}
═══════════════════════════════════

🎯 ОБЩАЯ СТАТИСТИКА:

Всего прогнозов: {stats['total']}
✅ Выиграно: {stats['won']}
❌ Проиграно: {stats['lost']}
⏳ Ожидают проверки: {stats['pending']}

{rate_emoji} Результативность: {stats['win_rate']}%

📊 ВИЗУАЛИЗАЦИЯ:
{wins_bar} {stats['win_rate']}% побед

---

📈 ПО ВИДАМ СПОРТА:
"""
        
        sport_icons = {
            'football': '⚽',
            'tennis': '🎾',
            'handball': '🤾'
        }
        
        sport_names = {
            'football': 'Футбол',
            'tennis': 'Теннис',
            'handball': 'Гандбол'
        }
        
        if stats['by_sport']:
            for sport, data in stats['by_sport'].items():
                icon = sport_icons.get(sport, '🏆')
                name = sport_names.get(sport, sport)
                total_checked = data['won'] + data['lost']
                bar = self._generate_progress_bar(data['win_rate'])
                message += f"\n{icon} {name}: {data['won']}/{total_checked} ({data['win_rate']:.0f}%)"
                message += f"\n   {bar}\n"
        else:
            message += "\nНет данных\n"
        
        message += "\n---\n\n⭐ ПО КАТЕГОРИЯМ:\n"
        
        category_names = {
            'dead': 'МЕРТВЫЕ (⭐⭐⭐⭐⭐)',
            'perfect': 'ИДЕАЛЬНЫЕ (⭐⭐⭐⭐)',
            'excellent': 'ОТЛИЧНЫЕ (⭐⭐⭐)',
            'good': 'ХОРОШИЕ (⭐⭐)'
        }
        
        if stats['by_category']:
            for category, data in stats['by_category'].items():
                name = category_names.get(category, category)
                total_checked = data['won'] + data['lost']
                bar = self._generate_progress_bar(data['win_rate'])
                message += f"\n{name}: {data['won']}/{total_checked} ({data['win_rate']:.0f}%)"
                message += f"\n   {bar}\n"
        else:
            message += "\nНет данных\n"
        
        message += "\n---\n\n📋 ДЕТАЛИ ПРОГНОЗОВ:\n"
        
        # Группируем по статусу
        won_preds = [p for p in stats['predictions'] if p['status'] == 'won']
        lost_preds = [p for p in stats['predictions'] if p['status'] == 'lost']
        
        category_map = {
            'dead': 'МЕРТВЫЙ ⭐⭐⭐⭐⭐',
            'perfect': 'ИДЕАЛЬНЫЙ ⭐⭐⭐⭐',
            'excellent': 'ОТЛИЧНЫЙ ⭐⭐⭐',
            'good': 'ХОРОШИЙ ⭐⭐'
        }
        
        if won_preds:
            message += f"\n✅ ВЫИГРАННЫЕ ({len(won_preds)}):\n"
            for i, p in enumerate(won_preds, 1):
                sport_icon = sport_icons.get(p['sport'], '🏆')
                category = category_map.get(p['category'], p['category'])
                league = p.get('league', '')
                message += f"\n{i}. {sport_icon} {p['team1']} - {p['team2']}"
                message += f"\n   {league} | Счет: {p['score_at_prediction']} → {p['final_score']}"
                message += f"\n   Коэфф: ~{p['odds']} | {category}\n"
        
        if lost_preds:
            message += f"\n❌ ПРОИГРАННЫЕ ({len(lost_preds)}):\n"
            for i, p in enumerate(lost_preds, 1):
                sport_icon = sport_icons.get(p['sport'], '🏆')
                category = category_map.get(p['category'], p['category'])
                league = p.get('league', '')
                message += f"\n{i}. {sport_icon} {p['team1']} - {p['team2']}"
                message += f"\n   {league} | Счет: {p['score_at_prediction']} → {p['final_score']}"
                message += f"\n   Коэфф: ~{p['odds']} | {category}\n"
        
        if stats['pending'] > 0:
            message += f"\n⏳ ОЖИДАЮТ ПРОВЕРКИ ({stats['pending']}):\n"
            pending_preds = [p for p in stats['predictions'] if p['status'] == 'pending']
            for i, p in enumerate(pending_preds, 1):
                sport_icon = sport_icons.get(p['sport'], '🏆')
                category = category_map.get(p['category'], p['category'])
                league = p.get('league', '')
                message += f"\n{i}. {sport_icon} {p['team1']} - {p['team2']}"
                message += f"\n   {league} | Прогноз в: {p['timestamp'].split('T')[1][:5]}"
                message += f"\n   Коэфф: ~{p['odds']} | {category}\n"
        
        message += "\n═══════════════════════════════════\n"
        message += "⏰ 23:45 МСК\n"
        message += "🤖 TrueLiveBet | Честная статистика\n"
        message += "═══════════════════════════════════\n\n"
        
        # Добавляем случайный дисклеймер
        disclaimer = self._get_random_disclaimer()
        message += f"⚠️ {disclaimer}"
        
        return message
    
    def generate_summary(self, stats):
        """Генерирует краткую сводку"""
        if not stats:
            return "❌ Нет данных"
        
        total_checked = stats['won'] + stats['lost']
        
        summary = f"""📊 КРАТКАЯ СВОДКА:
{stats['total']} прогнозов | {stats['won']}/{total_checked} выиграно | {stats['win_rate']}% результативность"""
        
        return summary
    
    def generate_full_report(self, date=None):
        """
        Генерирует полный отчет за день
        
        Args:
            date: Дата в формате 'YYYY-MM-DD' (если None - за сегодня)
        """
        stats = self.logger.get_statistics(date)
        
        if not stats:
            return "❌ Нет прогнозов за этот день"
        
        return self.generate_text_infographic(stats)
    
    def save_report_to_file(self, date=None, filename=None):
        """Сохраняет отчет в файл"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        if filename is None:
            filename = f"daily_report_{date}.txt"
        
        report = self.generate_full_report(date)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ Отчет сохранен в {filename}")
        return filename


# Пример использования
if __name__ == "__main__":
    generator = DailyStatsGenerator()
    
    print("="*70)
    print("📊 ГЕНЕРАЦИЯ ДНЕВНОГО ОТЧЕТА")
    print("="*70 + "\n")
    
    # Генерируем отчет за сегодня
    report = generator.generate_full_report()
    print(report)
    
    # Сохраняем в файл
    generator.save_report_to_file()

