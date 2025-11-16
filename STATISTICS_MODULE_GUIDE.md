# 📊 МОДУЛЬ СТАТИСТИКИ ПРОГНОЗОВ

## 🎯 НАЗНАЧЕНИЕ

Этот модуль автоматически:
1. **Логирует** все прогнозы в течение дня
2. **Проверяет** результаты матчей вечером
3. **Генерирует** красивую статистику и инфографику
4. **Отправляет** отчет в Telegram канал
5. **Сохраняет** данные для машинного обучения

---

## 📁 СТРУКТУРА ФАЙЛОВ

```
predictions_db/                  # База данных прогнозов
├── 2025-10-06/                 # Папка по дате
│   ├── match-1.json            # Детальная информация о прогнозе
│   ├── match-2.json
│   ├── predictions_log.csv     # Быстрая таблица за день
│   └── ...
├── 2025-10-07/
└── ...

prediction_logger.py             # Модуль логирования
prediction_checker.py            # Модуль проверки результатов
statistics_generator.py          # Генерация отчетов
send_daily_statistics.py         # Отправка в Telegram
```

---

## 🔧 УСТАНОВКА ЗАВИСИМОСТЕЙ

```bash
pip install matplotlib
```

---

## 📝 КАК ИСПОЛЬЗОВАТЬ

### 1️⃣ ЛОГИРОВАНИЕ ПРОГНОЗА (в процессе анализа)

Когда отправляешь прогноз в канал, одновременно логируй его:

```python
from prediction_logger import PredictionLogger

logger = PredictionLogger()

# Данные прогноза
prediction_data = {
    'timestamp': '2025-10-06 15:30:00',
    'sport': 'Футбол',
    'tournament': 'Экстракласа Польша',
    'team1': 'Ягеллония',
    'team2': 'Корона Кельце',
    'score_at_prediction': '2:0',
    'minute_at_prediction': '57',
    'recommendation': 'П1',
    'odds': 2.02,
    'category': 'ОТЛИЧНЫЙ ⭐⭐⭐',
    'reason': 'Фаворит ведет 2:0, 57 минута',
    'match_url': 'https://scores24.live/...',
    'league_position_team1': '5',
    'league_position_team2': '2',
    'stats_checked': ['Scores24', 'Flashscore'],
}

# Сохраняем
match_id = logger.log_prediction(prediction_data)
```

### 2️⃣ ПРОВЕРКА РЕЗУЛЬТАТОВ (вечером, автоматически)

```python
from prediction_checker import PredictionChecker

checker = PredictionChecker()

# Проверяем результат конкретного матча
checker.check_prediction_result('match-id', final_score='3:0')

# Или получаем статистику за день
stats = checker.get_daily_statistics()
print(f"Точность: {stats['accuracy']}%")
```

### 3️⃣ ГЕНЕРАЦИЯ ОТЧЕТОВ

```python
from statistics_generator import StatisticsGenerator

generator = StatisticsGenerator()

# Текстовый отчет
text_report = generator.generate_text_report()
print(text_report)

# Инфографика
generator.generate_infographic(output_file='stats_today.png')
```

### 4️⃣ АВТОМАТИЧЕСКАЯ ОТПРАВКА В TELEGRAM

```bash
python send_daily_statistics.py
```

Запускать вечером (например, в 23:00) через планировщик.

---

## ⏰ АВТОМАТИЗАЦИЯ

### Добавить в AutoHotkey скрипт:

```autohotkey
; Отправка ежедневной статистики в 23:00
if (currentHour = 23 and currentMinute = 0 and not sentStats23_00) {
    FileAppend, %A_Now% - Запуск отправки ежедневной статистики`n, working_autoclicker.log
    Run, python send_daily_statistics.py, D:\cursor\Backtothestart, Hide
    sentStats23_00 := true
}
```

---

## 📊 ФОРМАТ ДАННЫХ ДЛЯ ML

Каждый прогноз сохраняется в JSON с полной информацией:

```json
{
  "timestamp": "2025-10-06 15:30:00",
  "sport": "Футбол",
  "tournament": "Экстракласа Польша",
  "team1": "Ягеллония",
  "team2": "Корона Кельце",
  "score_at_prediction": "2:0",
  "minute_at_prediction": "57",
  "recommendation": "П1",
  "odds": 2.02,
  "category": "ОТЛИЧНЫЙ ⭐⭐⭐",
  "reason": "Фаворит ведет 2:0, 57 минута",
  "match_url": "https://scores24.live/...",
  "league_position_team1": "5",
  "league_position_team2": "2",
  "stats_checked": ["Scores24", "Flashscore"],
  "match_id": "ягеллония-vs-корона-кельце-2025-10-06",
  "final_result": "3:0",
  "prediction_correct": true,
  "checked_at": "2025-10-06 23:00:00"
}
```

### Фичи для ML:
- Вид спорта
- Турнир/лига
- Счет при прогнозе
- Минута прогноза
- Позиции в таблице
- Коэффициенты
- Категория прогноза
- Результат (правильный/неправильный)

---

## 📈 ПРИМЕР ОТЧЕТА

```
═══════════════════════════════════════
📊 СТАТИСТИКА ПРОГНОЗОВ ЗА 06.10.2025
═══════════════════════════════════════

📈 ОБЩАЯ СТАТИСТИКА:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Всего прогнозов: 10
✅ Правильных: 7
❌ Неправильных: 2
⏳ Ожидают результата: 1

🎯 ТОЧНОСТЬ: 77.78%

⚽🎾🤾 СТАТИСТИКА ПО ВИДАМ СПОРТА:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚽ Футбол: 5/7 (71.4%)
🎾 Теннис: 2/2 (100.0%)
🤾 Гандбол: 0/1 (0.0%)

⭐ СТАТИСТИКА ПО КАТЕГОРИЯМ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐⭐⭐⭐ ИДЕАЛЬНЫЙ: 3/4 (75.0%)
⭐⭐⭐ ОТЛИЧНЫЙ: 4/5 (80.0%)
⭐⭐ ХОРОШИЙ: 0/1 (0.0%)
```

---

## 🚀 ИНТЕГРАЦИЯ В ОСНОВНОЙ WORKFLOW

### В файле анализа добавь:

```python
from prediction_logger import PredictionLogger

logger = PredictionLogger()

# После отправки каждого прогноза в Telegram:
for match in suitable_matches:
    # ... формируем сообщение для Telegram ...
    
    # ЛОГИРУЕМ ПРОГНОЗ
    prediction_data = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'sport': match['sport'],
        'tournament': match['tournament'],
        'team1': match['team1'],
        'team2': match['team2'],
        'score_at_prediction': match['score'],
        'minute_at_prediction': match['minute'],
        'recommendation': match['recommendation'],
        'odds': match['odds'],
        'category': match['category'],
        'reason': match['analysis'],
        'match_url': match['url'],
        'league_position_team1': match['team1_position'],
        'league_position_team2': match['team2_position'],
        'stats_checked': match['sources_checked'],
    }
    
    logger.log_prediction(prediction_data)
```

---

## ✅ ПРЕИМУЩЕСТВА СИСТЕМЫ

1. **Прозрачность** - подписчики видят реальную статистику
2. **Автоматизация** - все работает само
3. **ML-готовность** - данные в структурированном формате
4. **Визуализация** - красивая инфографика
5. **История** - все сохраняется навсегда
6. **Аналитика** - статистика по категориям, спортам, турнирам

---

## 🔮 БУДУЩИЕ ВОЗМОЖНОСТИ

- Машинное обучение на основе исторических данных
- Предсказание точности прогноза до его отправки
- Автоматическая корректировка категорий
- Анализ трендов (какие турниры/команды лучше прогнозируются)
- Персонализация для подписчиков (какие прогнозы им подходят)

---

**Создано:** 06.10.2025  
**Версия:** 1.0  
**Статус:** Готово к использованию

