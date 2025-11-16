#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Импорт сегодняшних результатов из истории ставок BetBoom
"""

from results_tracker import add_result
from datetime import datetime
from zoneinfo import ZoneInfo

# Сегодняшние выигрышные ставки из скриншотов истории BetBoom
today_results = [
    {
        "sport": "football",
        "tournament": "Замбия. Суперлига",
        "home_team": "Пауер Динамос",
        "away_team": "Кансанши Динамос",
        "bet_outcome": "П1",
        "coefficient": 1.09,
        "stake_rub": 50.0,
        "payout_rub": 54.0,
        "ticket_id": "503462578",
        "match_time": "13 нояб 16:00",
        "score_at_bet": "[29m, 1:0 (1:0, 0:0)] [1st half]",
        "result_status": "win",
        "notes": "Выигрыш по основному времени",
    },
    {
        "sport": "tennis",
        "tournament": "ATP Challenger. Лион. Хард. Франция",
        "home_team": "Штруфф Я-Л.",
        "away_team": "Коприва В.",
        "bet_outcome": "П1",
        "coefficient": 1.05,
        "stake_rub": 50.0,
        "payout_rub": 52.0,
        "ticket_id": "4768769",
        "match_time": "13 нояб 16:45",
        "score_at_bet": "1:0 (6:1, 1:0, 0:0)",
        "result_status": "win",
        "notes": "Выигрыш матча",
    },
    {
        "sport": "tennis",
        "tournament": "ITF 25. Колумбус. Хард. США",
        "home_team": "Лилов В.",
        "away_team": "Янкандж В.",
        "bet_outcome": "П1",
        "coefficient": 1.09,
        "stake_rub": 50.0,
        "payout_rub": 54.0,
        "ticket_id": "17799824",
        "match_time": "13 нояб 21:15",
        "score_at_bet": "[0:0 (4:1, 0:0, 0:0) (40:A)-1] [1st set]",
        "result_status": "win",
        "notes": "Выигрыш матча",
    },
    {
        "sport": "tennis",
        "tournament": "ITF 50. Жен. Остин. Хард. США",
        "home_team": "Гасанова А.",
        "away_team": "Сиг М.",
        "bet_outcome": "П1",
        "coefficient": 1.02,
        "stake_rub": 50.0,
        "payout_rub": 51.0,
        "ticket_id": "595357052",
        "match_time": "13 нояб 21:20",
        "score_at_bet": "[0:0 (5:2, 0:0, 0:0) (15:15)-1] [1st set]",
        "result_status": "win",
        "notes": "Выигрыш матча",
    },
    {
        "sport": "handball",
        "tournament": "Германия. Бундеслига. Основное время",
        "home_team": "Фриш Гёппинген",
        "away_team": "Гамбург",
        "bet_outcome": "П1",
        "coefficient": 1.06,
        "stake_rub": 50.0,
        "payout_rub": 53.0,
        "ticket_id": "1857441306",
        "match_time": "13 нояб 21:00",
        "score_at_bet": "[52m, 29:25 (16:14, 13:11)] [2nd half]",
        "result_status": "win",
        "notes": "Выигрыш по основному времени",
    },
    {
        "sport": "tennis",
        "tournament": "ATP Challenger. Лион. Хард. Пары",
        "home_team": "Трак П./Идальго Д.",
        "away_team": "Романо Ф./Маэстрелли Ф.",
        "bet_outcome": "П1",
        "coefficient": 1.06,
        "stake_rub": 50.0,
        "payout_rub": 53.0,
        "ticket_id": "494525975",
        "match_time": "13 нояб 13:00",
        "score_at_bet": "0:0 (5:2, 0:0, 0:0)",
        "result_status": "win",
        "notes": "Выигрыш матча (пары)",
    },
    {
        "sport": "tennis",
        "tournament": "ITF 25. Колумбус. Хард. США",
        "home_team": "Лехно-Васютинский Ф.",
        "away_team": "Кокс Н.",
        "bet_outcome": "П1",
        "coefficient": 1.04,
        "stake_rub": 50.0,
        "payout_rub": 52.0,
        "ticket_id": "113705380",
        "match_time": "13 нояб 20:40",
        "score_at_bet": "[1:0 (6:2, 0:0, 0:0) (0:0)-1] [2nd set]",
        "result_status": "win",
        "notes": "Выигрыш матча",
    },
]

def main():
    print("=" * 70)
    print("ИМПОРТ РЕЗУЛЬТАТОВ ЗА 13 НОЯБРЯ 2025")
    print("=" * 70)
    
    imported = 0
    for result in today_results:
        try:
            add_result(**result)
            imported += 1
            print(f"[OK] Импортирован: {result['sport']} - {result['home_team']} vs {result['away_team']}")
        except Exception as e:
            print(f"[ERROR] Ошибка при импорте {result['home_team']} vs {result['away_team']}: {e}")
    
    print(f"\nИмпортировано результатов: {imported} из {len(today_results)}")
    
    # Показываем статистику
    from results_tracker import get_statistics
    stats = get_statistics(start_date="2025-11-13", end_date="2025-11-13")
    
    print("\n" + "=" * 70)
    print("СТАТИСТИКА ЗА 13 НОЯБРЯ 2025")
    print("=" * 70)
    print(f"Всего ставок: {stats['total_bets']}")
    print(f"Выигрышей: {stats['wins']}")
    print(f"Проигрышей: {stats['losses']}")
    print(f"Винрейт: {stats['win_rate']:.2f}%")
    print(f"Общая ставка: {stats['total_stake']:.2f} руб")
    print(f"Общий выигрыш: {stats['total_payout']:.2f} руб")
    print(f"Прибыль: {stats['total_profit']:.2f} руб")
    print(f"ROI: {stats['roi']:.2f}%")
    
    if stats['by_sport']:
        print("\nПо видам спорта:")
        for sport, data in stats['by_sport'].items():
            print(f"  {sport}: {data['bets']} ставок, {data['wins']} выигрышей, "
                  f"винрейт {data['win_rate']:.2f}%, прибыль {data['profit']:.2f} руб")

if __name__ == "__main__":
    main()

