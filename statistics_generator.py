# -*- coding: utf-8 -*-
"""
МОДУЛЬ ГЕНЕРАЦИИ СТАТИСТИКИ И ИНФОГРАФИКИ
Создает красивые отчеты для Telegram канала
"""
import json
import os
from datetime import datetime
from prediction_checker import PredictionChecker
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Для работы без GUI

class StatisticsGenerator:
    def __init__(self, db_path="predictions_db"):
        self.checker = PredictionChecker(db_path)
        self.today = datetime.now().strftime("%Y-%m-%d")
    
    def generate_text_report(self, date=None):
        """
        Генерирует текстовый отчет для Telegram
        """
        if date is None:
            date = self.today
        
        stats = self.checker.get_daily_statistics(date)
        
        if not stats or stats['total'] == 0:
            return "📭 Сегодня прогнозов не было"
        
        # Форматируем дату
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        date_formatted = date_obj.strftime("%d.%m.%Y")
        
        report = f"""
═══════════════════════════════════════
📊 СТАТИСТИКА ПРОГНОЗОВ ЗА {date_formatted}
═══════════════════════════════════════

📈 ОБЩАЯ СТАТИСТИКА:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Всего прогнозов: {stats['total']}
✅ Правильных: {stats['correct']}
❌ Неправильных: {stats['incorrect']}
⏳ Ожидают результата: {stats['pending']}

🎯 ТОЧНОСТЬ: {stats['accuracy']}%

"""
        
        if stats['by_sport']:
            report += "⚽🎾🤾 СТАТИСТИКА ПО ВИДАМ СПОРТА:\n"
            report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for sport, data in stats['by_sport'].items():
                if data['total'] > 0:
                    accuracy = round((data['correct'] / data['total']) * 100, 1) if data['total'] > 0 else 0
                    emoji = self._get_sport_emoji(sport)
                    report += f"{emoji} {sport}: {data['correct']}/{data['total']} ({accuracy}%)\n"
            report += "\n"
        
        if stats['by_category']:
            report += "⭐ СТАТИСТИКА ПО КАТЕГОРИЯМ:\n"
            report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for category, data in stats['by_category'].items():
                if data['total'] > 0:
                    accuracy = round((data['correct'] / data['total']) * 100, 1) if data['total'] > 0 else 0
                    stars = self._get_category_stars(category)
                    report += f"{stars} {category}: {data['correct']}/{data['total']} ({accuracy}%)\n"
            report += "\n"
        
        # Детальный список прогнозов
        report += "📋 ДЕТАЛЬНЫЙ СПИСОК:\n"
        report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for idx, pred in enumerate(stats['predictions'], 1):
            status = "✅" if pred['prediction_correct'] is True else ("❌" if pred['prediction_correct'] is False else "⏳")
            emoji = self._get_sport_emoji(pred['sport'])
            
            report += f"{idx}. {status} {emoji} {pred['team1']} - {pred['team2']}\n"
            report += f"   Прогноз: {pred['recommendation']} (коэф. {pred['odds']})\n"
            report += f"   Счет при прогнозе: {pred['score_at_prediction']} ({pred['minute_at_prediction']})\n"
            if pred['final_result']:
                report += f"   Финальный счет: {pred['final_result']}\n"
            report += "\n"
        
        report += "═══════════════════════════════════════\n"
        report += "🎯 TrueLiveBet — честная статистика\n"
        report += "💬 Все данные проверяются автоматически\n"
        report += "═══════════════════════════════════════"
        
        return report
    
    def generate_infographic(self, date=None, output_file=None):
        """
        Генерирует инфографику (изображение) для Telegram
        """
        if date is None:
            date = self.today
        
        if output_file is None:
            output_file = f"statistics_{date}.png"
        
        stats = self.checker.get_daily_statistics(date)
        
        if not stats or stats['total'] == 0:
            return None
        
        # Создаем фигуру с несколькими графиками
        fig = plt.figure(figsize=(12, 8))
        fig.suptitle(f'📊 Статистика прогнозов за {date}', fontsize=16, fontweight='bold')
        
        # 1. Круговая диаграмма общей статистики
        ax1 = plt.subplot(2, 2, 1)
        if stats['correct'] + stats['incorrect'] > 0:
            labels = ['Правильные ✅', 'Неправильные ❌']
            sizes = [stats['correct'], stats['incorrect']]
            colors = ['#4CAF50', '#F44336']
            explode = (0.1, 0)
            
            ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
                   autopct='%1.1f%%', shadow=True, startangle=90)
            ax1.set_title(f"Точность: {stats['accuracy']}%")
        
        # 2. Столбчатая диаграмма по видам спорта
        ax2 = plt.subplot(2, 2, 2)
        if stats['by_sport']:
            sports = list(stats['by_sport'].keys())
            correct = [stats['by_sport'][s]['correct'] for s in sports]
            incorrect = [stats['by_sport'][s]['incorrect'] for s in sports]
            
            x = range(len(sports))
            width = 0.35
            
            ax2.bar([i - width/2 for i in x], correct, width, label='Правильные', color='#4CAF50')
            ax2.bar([i + width/2 for i in x], incorrect, width, label='Неправильные', color='#F44336')
            
            ax2.set_xlabel('Вид спорта')
            ax2.set_ylabel('Количество')
            ax2.set_title('Статистика по видам спорта')
            ax2.set_xticks(x)
            ax2.set_xticklabels(sports, rotation=45, ha='right')
            ax2.legend()
            ax2.grid(axis='y', alpha=0.3)
        
        # 3. Столбчатая диаграмма по категориям
        ax3 = plt.subplot(2, 2, 3)
        if stats['by_category']:
            categories = list(stats['by_category'].keys())
            correct = [stats['by_category'][c]['correct'] for c in categories]
            incorrect = [stats['by_category'][c]['incorrect'] for c in categories]
            
            x = range(len(categories))
            width = 0.35
            
            ax3.bar([i - width/2 for i in x], correct, width, label='Правильные', color='#4CAF50')
            ax3.bar([i + width/2 for i in x], incorrect, width, label='Неправильные', color='#F44336')
            
            ax3.set_xlabel('Категория')
            ax3.set_ylabel('Количество')
            ax3.set_title('Статистика по категориям')
            ax3.set_xticks(x)
            ax3.set_xticklabels(categories, rotation=45, ha='right')
            ax3.legend()
            ax3.grid(axis='y', alpha=0.3)
        
        # 4. Текстовая сводка
        ax4 = plt.subplot(2, 2, 4)
        ax4.axis('off')
        
        summary_text = f"""
        📊 ИТОГОВАЯ СТАТИСТИКА
        
        Всего прогнозов: {stats['total']}
        ✅ Правильных: {stats['correct']}
        ❌ Неправильных: {stats['incorrect']}
        ⏳ Ожидают: {stats['pending']}
        
        🎯 Точность: {stats['accuracy']}%
        
        🎯 TrueLiveBet
        Честная статистика прогнозов
        """
        
        ax4.text(0.1, 0.5, summary_text, fontsize=12, verticalalignment='center',
                fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Инфографика сохранена: {output_file}")
        return output_file
    
    def _get_sport_emoji(self, sport):
        """Возвращает эмодзи для вида спорта"""
        emojis = {
            'Футбол': '⚽',
            'Теннис': '🎾',
            'Гандбол': '🤾',
            'Баскетбол': '🏀',
            'Хоккей': '🏒'
        }
        return emojis.get(sport, '🏆')
    
    def _get_category_stars(self, category):
        """Возвращает звезды для категории"""
        stars = {
            'МЕРТВЫЙ': '⭐⭐⭐⭐⭐',
            'ИДЕАЛЬНЫЙ': '⭐⭐⭐⭐',
            'ОТЛИЧНЫЙ': '⭐⭐⭐',
            'ХОРОШИЙ': '⭐⭐'
        }
        return stars.get(category, '⭐')


# ПРИМЕР ИСПОЛЬЗОВАНИЯ
if __name__ == "__main__":
    generator = StatisticsGenerator()
    
    # Генерируем текстовый отчет
    report = generator.generate_text_report()
    print(report)
    
    # Генерируем инфографику
    # generator.generate_infographic()
    print("\n✅ Отчет готов для отправки в Telegram!")

