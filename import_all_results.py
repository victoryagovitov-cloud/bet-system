#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Импорт всех результатов ставок из истории BetBoom
"""

from results_tracker import add_result
from datetime import datetime
from zoneinfo import ZoneInfo

# Все результаты из скриншотов истории ставок
all_results = [
    # 12 ноября 2025
    {
        "sport": "football",
        "tournament": "Англия. Кубок лиги. Жен",
        "home_team": "Вест Хэм Юн (ж)",
        "away_team": "Саутгемптон ЖФК (ж)",
        "bet_outcome": "П1",
        "coefficient": 1.1,
        "stake_rub": 50.0,
        "payout_rub": 55.0,
        "ticket_id": "1564990506",
        "match_time": "12 нояб. в 22:00",
        "score_at_bet": "[73m, 1:0 (0:0, 1:0)] [2nd half]",
        "result_status": "win",
        "notes": "Выигрыш по основному времени",
    },
    {
        "sport": "tennis",
        "tournament": "ATP Challenger. Шампейн. Хард. США",
        "home_team": "Штебе С.-М.",
        "away_team": "Хара Френд Д. Д.",
        "bet_outcome": "П1",
        "coefficient": 1.01,
        "stake_rub": 100.0,
        "payout_rub": 101.0,
        "ticket_id": "1610879009",
        "match_time": "12 нояб. в 22:00",
        "score_at_bet": "1:0 (7:6, 5:3, 0:0)",
        "result_status": "win",
        "notes": "Выигрыш матча",
    },
    {
        "sport": "tennis",
        "tournament": "ATP Finals. Турин. Хард. Италия",
        "home_team": "Синнер Я.",
        "away_team": "Зверев А.",
        "bet_outcome": "П1",
        "coefficient": 1.06,
        "stake_rub": 50.0,
        "payout_rub": 53.0,
        "ticket_id": "1201417192",
        "match_time": "12 нояб. в 22:30",
        "score_at_bet": "1:0 (6:4, 2:1, 0:0)",
        "result_status": "win",
        "notes": "Выигрыш матча",
    },
    {
        "sport": "tennis",
        "tournament": "ATP Challenger. Монтевидео. Грунт.",
        "home_team": "Кестельбойм М./Дюран Г.",
        "away_team": "Демолинер М./Баррьентос Н.",
        "bet_outcome": "П2",
        "coefficient": 1.2,
        "stake_rub": 50.0,
        "payout_rub": 60.0,
        "ticket_id": "168566962",
        "match_time": "12 нояб. в 23:00",
        "score_at_bet": "0:1 (1:6, 1:1, 0:0)",
        "result_status": "win",
        "notes": "Выигрыш матча (пары)",
    },
    {
        "sport": "football",
        "tournament": "BetBoom Матчи Сборной России",
        "home_team": "Россия",
        "away_team": "Перу",
        "bet_outcome": "П1",
        "coefficient": 1.13,
        "stake_rub": 50.0,
        "payout_rub": 0.0,
        "ticket_id": "1903524285",
        "match_time": "12 нояб. в 20:05",
        "score_at_bet": "[53m, 1:0 (1:0, 0:0)] [2nd half]",
        "result_status": "loss",
        "notes": "Проигрыш - матч завершился ничьей или поражением",
    },
    {
        "sport": "football",
        "tournament": "Иордания. 1-й дивизион",
        "home_team": "Сама Клуб",
        "away_team": "Шабаб Аль Акаба",
        "bet_outcome": "П1",
        "coefficient": 1.03,
        "stake_rub": 50.0,
        "payout_rub": 51.0,
        "ticket_id": "631213736",
        "match_time": "12 нояб. в 19:30",
        "score_at_bet": "[86m, 2:1 (0:1, 2:0)] [2nd half]",
        "result_status": "win",
        "notes": "Выигрыш по основному времени",
    },
    {
        "sport": "football",
        "tournament": "Катар. Чемпионат U19",
        "home_team": "Аль Райан U19",
        "away_team": "Катар СК Доха U19",
        "bet_outcome": "П1",
        "coefficient": 1.03,
        "stake_rub": 50.0,
        "payout_rub": 51.0,
        "ticket_id": "153543368",
        "match_time": "12 нояб. в 19:20",
        "score_at_bet": "[89m, 2:1 (1:1, 1:0)] [2nd half]",
        "result_status": "win",
        "notes": "Выигрыш по основному времени",
    },
    # 11 ноября 2025
    {
        "sport": "tennis",
        "tournament": "ATP Challenger. Монтевидео. Грунт.",
        "home_team": "Дутра Да Сильва Д.",
        "away_team": "Нава Э.",
        "bet_outcome": "П2",
        "coefficient": 1.04,
        "stake_rub": 50.0,
        "payout_rub": 52.0,
        "ticket_id": "1414262625",
        "match_time": "11 нояб. в 19:30",
        "score_at_bet": "0:1 (2:6, 2:1, 0:0)",
        "result_status": "win",
        "notes": "Выигрыш матча",
    },
    {
        "sport": "football",
        "tournament": "Англия. Кубок. EFL Trophy",
        "home_team": "Джиллингем",
        "away_team": "Уикомб Уондерерс",
        "bet_outcome": "П2",
        "coefficient": 1.14,
        "stake_rub": 50.0,
        "payout_rub": 57.0,
        "ticket_id": "793717818",
        "match_time": "11 нояб. в 22:00",
        "score_at_bet": "0:1 (0:1)",
        "result_status": "win",
        "notes": "Выигрыш по основному времени",
    },
    {
        "sport": "football",
        "tournament": "Англия. Кубок. EFL Trophy",
        "home_team": "Олдхэм Атлетик",
        "away_team": "Болтон Уондерерс",
        "bet_outcome": "П2",
        "coefficient": 1.01,
        "stake_rub": 100.0,
        "payout_rub": 101.0,
        "ticket_id": "1103805289",
        "match_time": "11 нояб. в 22:00",
        "score_at_bet": "0:2 (0:1, 0:1)",
        "result_status": "win",
        "notes": "Выигрыш по основному времени",
    },
    {
        "sport": "tennis",
        "tournament": "ATP Challenger. Лион. Хард. Пары",
        "home_team": "Прашант В./Кадхе А.",
        "away_team": "Донски А./Молчанов Д.",
        "bet_outcome": "П1",
        "coefficient": 1.09,
        "stake_rub": 50.0,
        "payout_rub": 54.0,
        "ticket_id": "607825277",
        "match_time": "11 нояб. в 18:55",
        "score_at_bet": "1:0 (7:5, 6:6, 0:0)",
        "result_status": "win",
        "notes": "Выигрыш матча (пары)",
    },
    # 10 ноября 2025
    {
        "sport": "football",
        "tournament": "Дания. 1-й дивизион",
        "home_team": "Эсбьерг",
        "away_team": "Мидделфарт",
        "bet_outcome": "П1",
        "coefficient": 1.18,
        "stake_rub": 50.0,
        "payout_rub": 59.0,
        "ticket_id": "404409452",
        "match_time": "10 нояб. в 21:00",
        "score_at_bet": "2:1 (2:1)",
        "result_status": "win",
        "notes": "Выигрыш по основному времени",
    },
]

def main():
    print("=" * 70)
    print("ИМПОРТ ВСЕХ РЕЗУЛЬТАТОВ ИЗ ИСТОРИИ СТАВОК")
    print("=" * 70)
    
    imported = 0
    errors = 0
    
    for result in all_results:
        try:
            add_result(**result)
            imported += 1
            status_icon = "[OK]" if result["result_status"] == "win" else "[LOSS]"
            print(f"{status_icon} {result['sport']} - {result['home_team']} vs {result['away_team']} "
                  f"(кэф {result['coefficient']}, {result['result_status']})")
        except Exception as e:
            errors += 1
            print(f"[ERROR] Ошибка при импорте {result.get('home_team', '?')}: {e}")
    
    print(f"\nИмпортировано: {imported} из {len(all_results)}")
    if errors > 0:
        print(f"Ошибок: {errors}")
    
    # Показываем общую статистику
    from results_tracker import get_statistics
    stats = get_statistics()
    
    print("\n" + "=" * 70)
    print("ОБЩАЯ СТАТИСТИКА СИСТЕМЫ")
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
        for sport, data in sorted(stats['by_sport'].items()):
            print(f"  {sport.upper()}: {data['bets']} ставок, {data['wins']} выигрышей, "
                  f"винрейт {data['win_rate']:.2f}%, прибыль {data['profit']:.2f} руб")

if __name__ == "__main__":
    main()

