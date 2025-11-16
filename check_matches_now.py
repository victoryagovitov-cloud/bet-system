#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from generate_live_report import generate_live_report

print("=" * 70)
print("ПРОВЕРКА: ЕСТЬ ЛИ ПОДХОДЯЩИЕ МАТЧИ ПРЯМО СЕЙЧАС")
print("=" * 70)

message, matches, context = generate_live_report(max_matches=5)

print(f"\nНайдено матчей: {len(matches)}")
print(f"\nКонтекст:")
for key, value in context.items():
    if key != "generated_at":
        print(f"  {key}: {value}")

if len(matches) == 0:
    print("\n" + "=" * 70)
    print("МАТЧЕЙ НЕ НАЙДЕНО")
    print("=" * 70)
    print("\nПроверяю детали из контекста...")
    
    football_total = context.get("football_total", 0)
    football_filtered = context.get("football_filtered", 0)
    football_passed = context.get("football_passed", 0)
    
    tennis_total = context.get("tennis_total", 0)
    tennis_filtered = context.get("tennis_filtered", 0)
    tennis_passed = context.get("tennis_passed", 0)
    
    print(f"\nФУТБОЛ:")
    print(f"  Всего найдено: {football_total}")
    print(f"  Отфильтровано: {football_filtered}")
    print(f"  Прошло фильтры: {football_passed}")
    
    print(f"\nТЕННИС:")
    print(f"  Всего найдено: {tennis_total}")
    print(f"  Отфильтровано: {tennis_filtered}")
    print(f"  Прошло фильтры: {tennis_passed}")
    
    if football_total == 0 and tennis_total == 0:
        print("\n[INFO] На Scores24 нет live матчей с статистикой прямо сейчас")
    elif football_passed == 0 and tennis_passed == 0:
        print("\n[INFO] Есть матчи, но они не прошли фильтры (слишком строгие требования)")
else:
    print("\n" + "=" * 70)
    print(f"НАЙДЕНО {len(matches)} МАТЧЕЙ")
    print("=" * 70)
    for i, match in enumerate(matches, 1):
        sport = match.get("sport", "unknown")
        home = match.get("home_team", "?")
        away = match.get("away_team", "?")
        odds = match.get("odds", {}).get("value", "?")
        dominance = match.get("dominance_score", "?")
        print(f"\n{i}. {sport.upper()}: {home} - {away}")
        print(f"   Коэффициент: {odds}, Dominance: {dominance}")

print("\n" + "=" * 70)
print("ПРОВЕРКА ЗАВЕРШЕНА")
print("=" * 70)

