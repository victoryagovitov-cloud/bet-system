#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("=" * 70)
print("ОБЪЯСНЕНИЕ: ЧТО ТАКОЕ 'СВОБОДНЫЕ СЛОТЫ'")
print("=" * 70)

print("\nМАКСИМУМ МАТЧЕЙ В СООБЩЕНИИ: 5")
print("Это означает, что в одном сообщении может быть максимум 5 матчей.")

print("\n" + "=" * 70)
print("ЛОГИКА РАСПРЕДЕЛЕНИЯ СЛОТОВ")
print("=" * 70)

print("\nШАГ 1: ФУТБОЛ (приоритет 1)")
print("-" * 70)
print("  - Система ищет футбольные матчи")
print("  - Заполняет слоты 1, 2, 3, 4, 5 (если есть)")
print("  - Пример: найдено 3 футбольных матча")
print("  - Результат: занято 3 слота, свободно 2 слота")

print("\nШАГ 2: ТЕННИС (приоритет 2)")
print("-" * 70)
print("  - Если футбола НЕТ (0 матчей):")
print("    -> Теннис получает минимум 1 слот")
print("  - Если футбол ЕСТЬ, но есть свободные слоты:")
print("    -> Теннис заполняет оставшиеся слоты")
print("  - Пример: футбол занял 3 слота, свободно 2")
print("  - Результат: теннис получает 2 слота")

print("\nШАГ 3: БАСКЕТБОЛ (приоритет 3)")
print("-" * 70)
print("  - Заполняет слоты, которые остались после футбола и тенниса")
print("  - Пример: футбол 3 + теннис 1 = занято 4, свободно 1")
print("  - Результат: баскетбол получает 1 слот")

print("\nШАГ 4: ГАНДБОЛ (приоритет 4)")
print("-" * 70)
print("  - Заполняет последние оставшиеся слоты")
print("  - Пример: футбол 2 + теннис 1 + баскетбол 1 = занято 4, свободно 1")
print("  - Результат: гандбол получает 1 слот")

print("\n" + "=" * 70)
print("ПРИМЕРЫ")
print("=" * 70)

examples = [
    {
        "name": "Пример 1: Много футбола",
        "football": 5,
        "tennis": 3,
        "basketball": 2,
        "handball": 1
    },
    {
        "name": "Пример 2: Нет футбола",
        "football": 0,
        "tennis": 3,
        "basketball": 2,
        "handball": 1
    },
    {
        "name": "Пример 3: Смешанный",
        "football": 2,
        "tennis": 1,
        "basketball": 1,
        "handball": 1
    },
    {
        "name": "Пример 4: Мало матчей",
        "football": 1,
        "tennis": 0,
        "basketball": 0,
        "handball": 0
    }
]

for example in examples:
    print(f"\n{example['name']}:")
    print(f"  Найдено: Футбол={example['football']}, Теннис={example['tennis']}, Баскетбол={example['basketball']}, Гандбол={example['handball']}")
    
    max_matches = 5
    football_selected = min(example['football'], max_matches)
    remaining = max_matches - football_selected
    
    if football_selected == 0:
        tennis_selected = min(example['tennis'], max(1, remaining))
    else:
        tennis_selected = min(example['tennis'], remaining)
    remaining -= tennis_selected
    
    basketball_selected = min(example['basketball'], remaining)
    remaining -= basketball_selected
    
    handball_selected = min(example['handball'], remaining)
    
    print(f"  В сообщении:")
    print(f"    Футбол: {football_selected}")
    print(f"    Теннис: {tennis_selected}")
    print(f"    Баскетбол: {basketball_selected}")
    print(f"    Гандбол: {handball_selected}")
    print(f"    Всего: {football_selected + tennis_selected + basketball_selected + handball_selected}")

print("\n" + "=" * 70)
print("ВЫВОД")
print("=" * 70)
print("\n'Свободные слоты' = оставшиеся места в сообщении (максимум 5)")
print("\nПриоритет:")
print("  1. Футбол заполняет сначала (если есть)")
print("  2. Теннис заполняет оставшееся (если есть свободные слоты)")
print("  3. Баскетбол заполняет оставшееся (если есть свободные слоты)")
print("  4. Гандбол заполняет оставшееся (если есть свободные слоты)")
print("\nЕсли футбола нет - теннис получает минимум 1 слот")
print("Если все слоты заняты футболом - другие виды спорта не попадают в сообщение")

