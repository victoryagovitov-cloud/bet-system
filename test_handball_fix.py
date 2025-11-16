#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graphql_handball_analyzer import analyze_live_handball_matches

print("Проверка исправления гандбола:")
print("=" * 60)

matches = analyze_live_handball_matches(limit=10)
print(f"Найдено матчей: {len(matches)}")

for i, m in enumerate(matches[:5], 1):
    teams = m['teams']
    score = m['score']
    minute_numeric = m.get('minute_numeric', 'N/A')
    total_score = m.get('total_score', 0)
    pace = m.get('pace', 0)
    projected_total = m.get('projected_total')
    
    print(f"\n{i}. {teams[0]} vs {teams[1]}")
    print(f"   Счет: {score}")
    print(f"   Минута: {minute_numeric}")
    print(f"   Всего голов: {total_score}")
    print(f"   Темп: {pace:.2f} гол/мин")
    if projected_total:
        print(f"   Прогнозный тотал: {projected_total:.1f}")
    
    # Проверка: темп не должен быть 1.0 если это не так
    if minute_numeric and total_score:
        calculated_pace = total_score / minute_numeric
        if abs(calculated_pace - pace) > 0.01:
            print(f"   [ОШИБКА] Темп не совпадает! Ожидалось {calculated_pace:.2f}, получено {pace:.2f}")
        elif calculated_pace == 1.0 and total_score == minute_numeric:
            print(f"   [ПРЕДУПРЕЖДЕНИЕ] Темп 1.0 - возможно, минута определена неправильно")
