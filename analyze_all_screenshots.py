#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Все ставки из скриншотов
all_bets = [
    # Выигрышные
    {"sport": "tennis", "coef": 1.01, "result": "win", "description": "Штебе С.-М. vs Хара Френд Д. Д.", "date": "12.11"},
    {"sport": "tennis", "coef": 1.20, "result": "win", "description": "Кестельбойм М./Дюран Г. vs Демолинер М./Баррьентос Н. (пары)", "date": "12.11"},
    {"sport": "tennis", "coef": 1.06, "result": "win", "description": "Синнер Я. vs Зверев А.", "date": "12.11"},
    {"sport": "football", "coef": 1.10, "result": "win", "description": "Вест Хэм (Ж) vs Саутгемптон (Ж)", "date": "12.11"},
    {"sport": "football", "coef": 1.03, "result": "win", "description": "Сама vs Аль Акаба", "date": "12.11"},
    {"sport": "football", "coef": 1.18, "result": "win", "description": "Эсбьерг vs Мидделфарт", "date": "10.11"},
    {"sport": "football", "coef": 1.03, "result": "win", "description": "Аль Райан U19 vs Катар СК Доха U19", "date": "12.11"},
    {"sport": "tennis", "coef": 1.09, "result": "win", "description": "Прашант В./Кадхе А. vs Донски А./Молчанов Д. (пары)", "date": "11.11"},
    {"sport": "football", "coef": 1.14, "result": "win", "description": "Джиллингем vs Уикомб Уондерерс", "date": "11.11"},
    {"sport": "tennis", "coef": 1.04, "result": "win", "description": "Дутра Да Сильва Д. vs Нава Э.", "date": "11.11"},
    {"sport": "football", "coef": 1.01, "result": "win", "description": "Олдхэм Атлетик vs Болтон Уондерерс", "date": "11.11"},
    
    # Проигрышные
    {"sport": "football", "coef": 1.13, "result": "loss", "description": "Россия vs Перу", "date": "12.11"},
    {"sport": "football", "coef": 1.01, "result": "loss", "description": "Португалия U19 vs Эстония U19 (в экспрессе)", "date": "12.11"},
    {"sport": "football", "coef": 1.05, "result": "loss", "description": "Нордшелланд (ж) vs Мура (ж) (в экспрессе, но выиграла)", "date": "12.11", "note": "Экспресс проиграл из-за первой ставки"},
]

# Фильтруем только ординары (не экспрессы)
ordinary_bets = [b for b in all_bets if "экспрессе" not in b["description"].lower()]

wins = [b for b in ordinary_bets if b["result"] == "win"]
losses = [b for b in ordinary_bets if b["result"] == "loss"]

win_coefs = [b["coef"] for b in wins]
loss_coefs = [b["coef"] for b in losses]
all_coefs = [b["coef"] for b in ordinary_bets]

print("=" * 70)
print("СТАТИСТИКА ПО ВСЕМ СКРИНАМ ИЗ BETBOOM")
print("=" * 70)

print(f"\nВСЕГО ОРДИНАРОВ: {len(ordinary_bets)}")
print(f"  Выигрышных: {len(wins)}")
print(f"  Проигрышных: {len(losses)}")

if len(wins) + len(losses) > 0:
    win_rate = (len(wins) / (len(wins) + len(losses))) * 100
    print(f"  Процент выигрышей: {win_rate:.1f}%")

print(f"\nКОЭФФИЦИЕНТЫ (все ставки):")
if all_coefs:
    print(f"  Всего: {len(all_coefs)}")
    print(f"  Средний: {sum(all_coefs)/len(all_coefs):.3f}")
    print(f"  Минимум: {min(all_coefs):.2f}")
    print(f"  Максимум: {max(all_coefs):.2f}")

print(f"\nКОЭФФИЦИЕНТЫ ВЫИГРЫШНЫХ:")
if win_coefs:
    print(f"  Всего: {len(win_coefs)}")
    print(f"  Средний: {sum(win_coefs)/len(win_coefs):.3f}")
    print(f"  Минимум: {min(win_coefs):.2f}")
    print(f"  Максимум: {max(win_coefs):.2f}")

print(f"\nКОЭФФИЦИЕНТЫ ПРОИГРЫШНЫХ:")
if loss_coefs:
    print(f"  Всего: {len(loss_coefs)}")
    print(f"  Средний: {sum(loss_coefs)/len(loss_coefs):.3f}")
    print(f"  Минимум: {min(loss_coefs):.2f}")
    print(f"  Максимум: {max(loss_coefs):.2f}")

print(f"\nПО ВИДАМ СПОРТА:")
football_bets = [b for b in ordinary_bets if b["sport"] == "football"]
tennis_bets = [b for b in ordinary_bets if b["sport"] == "tennis"]

football_wins = len([b for b in football_bets if b["result"] == "win"])
football_losses = len([b for b in football_bets if b["result"] == "loss"])
tennis_wins = len([b for b in tennis_bets if b["result"] == "win"])
tennis_losses = len([b for b in tennis_bets if b["result"] == "loss"])

print(f"  Футбол: {len(football_bets)} ставок ({football_wins} выигрышных, {football_losses} проигрышных)")
print(f"  Теннис: {len(tennis_bets)} ставок ({tennis_wins} выигрышных, {tennis_losses} проигрышных)")

print(f"\nДЕТАЛИ ВЫИГРЫШНЫХ СТАВОК:")
for i, bet in enumerate(wins, 1):
    print(f"  {i}. {bet['description']}")
    print(f"     Кэф: {bet['coef']:.2f}, Дата: {bet['date']}")

if losses:
    print(f"\nДЕТАЛИ ПРОИГРЫШНЫХ СТАВОК:")
    for i, bet in enumerate(losses, 1):
        print(f"  {i}. {bet['description']}")
        print(f"     Кэф: {bet['coef']:.2f}, Дата: {bet['date']}")

print("\n" + "=" * 70)
print("ПРИМЕЧАНИЕ: Экспрессы не учитываются в статистике ординаров")
print("=" * 70)

