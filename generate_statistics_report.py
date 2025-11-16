#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генерация подробного статистического отчета по системе
"""

from results_tracker import get_statistics
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

def generate_report():
    """Генерирует подробный статистический отчет."""
    
    # Статистика за сегодня
    today = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d")
    today_stats = get_statistics(start_date=today, end_date=today)
    
    # Общая статистика (все время)
    all_time_stats = get_statistics()
    
    report = []
    report.append("=" * 70)
    report.append("СТАТИСТИЧЕСКИЙ ОТЧЕТ ПО СИСТЕМЕ LIVE-СТАВОК")
    report.append("=" * 70)
    report.append(f"Дата отчета: {datetime.now(ZoneInfo('Europe/Moscow')).strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Статистика за сегодня
    report.append("СТАТИСТИКА ЗА СЕГОДНЯ (13 НОЯБРЯ 2025)")
    report.append("-" * 70)
    report.append(f"Всего ставок: {today_stats['total_bets']}")
    report.append(f"Выигрышей: {today_stats['wins']}")
    report.append(f"Проигрышей: {today_stats['losses']}")
    report.append(f"Винрейт: {today_stats['win_rate']:.2f}%")
    report.append(f"Общая ставка: {today_stats['total_stake']:.2f} руб")
    report.append(f"Общий выигрыш: {today_stats['total_payout']:.2f} руб")
    report.append(f"Прибыль: {today_stats['total_profit']:.2f} руб")
    report.append(f"ROI: {today_stats['roi']:.2f}%")
    report.append("")
    
    if today_stats['by_sport']:
        report.append("По видам спорта (сегодня):")
        for sport, data in sorted(today_stats['by_sport'].items()):
            report.append(f"  {sport.upper()}:")
            report.append(f"    Ставок: {data['bets']}")
            report.append(f"    Выигрышей: {data['wins']}")
            report.append(f"    Винрейт: {data['win_rate']:.2f}%")
            report.append(f"    Ставка: {data['stake']:.2f} руб")
            report.append(f"    Выигрыш: {data['payout']:.2f} руб")
            report.append(f"    Прибыль: {data['profit']:.2f} руб")
            report.append("")
    
    # Общая статистика
    report.append("=" * 70)
    report.append("ОБЩАЯ СТАТИСТИКА (ВСЕ ВРЕМЯ)")
    report.append("-" * 70)
    report.append(f"Всего ставок: {all_time_stats['total_bets']}")
    report.append(f"Выигрышей: {all_time_stats['wins']}")
    report.append(f"Проигрышей: {all_time_stats['losses']}")
    report.append(f"Винрейт: {all_time_stats['win_rate']:.2f}%")
    report.append(f"Общая ставка: {all_time_stats['total_stake']:.2f} руб")
    report.append(f"Общий выигрыш: {all_time_stats['total_payout']:.2f} руб")
    report.append(f"Прибыль: {all_time_stats['total_profit']:.2f} руб")
    report.append(f"ROI: {all_time_stats['roi']:.2f}%")
    report.append("")
    
    if all_time_stats['by_sport']:
        report.append("По видам спорта (все время):")
        for sport, data in sorted(all_time_stats['by_sport'].items()):
            report.append(f"  {sport.upper()}:")
            report.append(f"    Ставок: {data['bets']}")
            report.append(f"    Выигрышей: {data['wins']}")
            report.append(f"    Винрейт: {data['win_rate']:.2f}%")
            report.append(f"    Ставка: {data['stake']:.2f} руб")
            report.append(f"    Выигрыш: {data['payout']:.2f} руб")
            report.append(f"    Прибыль: {data['profit']:.2f} руб")
            report.append("")
    
    # Анализ эффективности
    report.append("=" * 70)
    report.append("АНАЛИЗ ЭФФЕКТИВНОСТИ")
    report.append("-" * 70)
    
    if today_stats['total_bets'] > 0:
        avg_coefficient = today_stats['total_payout'] / today_stats['total_stake'] if today_stats['total_stake'] > 0 else 0
        report.append(f"Средний коэффициент (сегодня): {avg_coefficient:.3f}")
        report.append(f"Средняя ставка: {today_stats['total_stake'] / today_stats['total_bets']:.2f} руб")
        report.append(f"Средний выигрыш: {today_stats['total_payout'] / today_stats['total_bets']:.2f} руб")
        report.append(f"Средняя прибыль на ставку: {today_stats['total_profit'] / today_stats['total_bets']:.2f} руб")
    
    report.append("")
    report.append("=" * 70)
    
    return "\n".join(report)

def main():
    report = generate_report()
    print(report)
    
    # Сохраняем в файл
    report_file = Path("data/statistics_report.txt")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with report_file.open("w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\nОтчет сохранен в: {report_file}")

if __name__ == "__main__":
    main()

