# 📱 Интеграция Telegram - Полное руководство

## ✅ Что уже есть в папке проекта

### Готовые скрипты отправки:
1. **`telegram_simple.py`** - базовая отправка
2. **`send_fixed_analysis.py`** - улучшенная версия
3. **`config.json`** - конфигурация с токеном и каналом

### Новые скрипты (созданы):
1. **`analyze_and_send_telegram.py`** ⭐ - ОСНОВНОЙ скрипт (анализ + отправка)
2. **`ahk_trigger_handler.py`** - обработчик сигналов от AutoHotkey

---

## 🚀 Быстрый старт

### Вариант 1: Запустить анализ и отправить в Telegram сейчас

```bash
python analyze_and_send_telegram.py
```

**Результат:**
- ✅ Анализирует тестовые матчи (или реальные через Browser MCP)
- ✅ Форматирует сообщение
- ✅ Отправляет в @TrueLiveBet
- ✅ Сохраняет копию в `last_telegram_message.txt`

---

### Вариант 2: Обработка сигналов от AutoHotkey

```bash
# Одноразовый запуск анализа
python ahk_trigger_handler.py run

# Или мониторить сигналы (ждать 🎯F)
python ahk_trigger_handler.py monitor
```

---

## 📋 Структура решения

### `analyze_and_send_telegram.py`

**Шаг 1: Анализ матчей**
```python
recommendations = analyze_matches(matches_data)
# Фильтрует только неничейные матчи
# Определяет фаворита по коэффициентам
# Проверяет: ведет ли фаворит?
# Возвращает список подходящих матчей
```

**Шаг 2: Форматирование для Telegram**
```python
telegram_message = format_telegram_message(recommendations)
# Создает красивое сообщение по шаблону
# Если матчей нет - отправляет "нет подходящих"
# Если есть - выводит каждый с обоснованием
```

**Шаг 3: Отправка**
```python
success = send_to_telegram(telegram_message)
# Делает POST запрос к Telegram API
# Отправляет в @TrueLiveBet
```

---

## 🔌 Интеграция с Browser MCP

Когда потребуется получать реальные данные:

```python
# В analyze_and_send_telegram.py добавить:
from browser_based_analyzer import get_real_betboom_data

def main(matches_data=None):
    if matches_data is None:
        # Получить реальные данные с BetBoom через MCP
        matches_data = get_real_betboom_data()
    
    recommendations = analyze_matches(matches_data)
    # ... остальное
```

---

## 📱 Формат сообщения в @TrueLiveBet

```
🎯 LIVE-АНАЛИЗ • 14:25 МСК, 09.11.2025

—————————————

⚽ ФУТБОЛ ⚽

1. Боде Глимт vs Брюн

   Счет: 1-0 (1Т, 16 мин) | Норвегия. Элитсерия

   🎯 Рекомендуем: Боде Глимт

   📊 Обоснование:
   • Боде Глимт - фаворит (🔥 кэф 1.03)
   • На поле контролирует (счет 1-0)

   💰 Кэф BetBoom: ~1.03

—————————————

📌 Важные моменты:
  • Все рекомендации основаны на анализе лайв-данных
  • Ставим только на матчи где фаворит лидирует
  • Размер ставки - только из собственного банка

—————————————

⚠️ Дисклеймер: Беттинг связан с рисками...

🤝 @TrueLiveBet — честный ИИ-анализ лайв-ставок
```

---

## 🔑 Ключевые параметры

### `config.json`
```json
{
  "notifications": {
    "telegram": {
      "bot_token": "7824400107:AAGZqPdS0E0N3HsYpD8TW9m8c-bapFd-RHk",
      "channel_username": "@TrueLiveBet"
    }
  }
}
```

### Переменные в скриптах
```python
BOT_TOKEN = '7824400107:AAGZqPdS0E0N3HsYpD8TW9m8c-bapFd-RHk'
CHANNEL_ID = '@TrueLiveBet'
```

---

## 🔄 Полный цикл работы (с AutoHotkey)

```
1. AutoHotkey отправляет сигнал 🎯F каждые 45 минут
                ↓
2. Cursor получает сигнал в чате
                ↓
3. Срабатывает ahk_trigger_handler.py run
                ↓
4. Получаются данные с BetBoom (через Browser MCP или готовые)
                ↓
5. Запускается analyze_matches()
                ↓
6. Форматируется сообщение для Telegram
                ↓
7. Отправляется в @TrueLiveBet
                ↓
8. Результат логируется в ahk_trigger.log
```

---

## 📝 Логирование

### Файл `ahk_trigger.log`
```
[2025-11-09 14:25:30] START: ================================================================================
[2025-11-09 14:25:30] INFO: Получен сигнал от AutoHotkey - начинаем анализ
[2025-11-09 14:25:31] INFO: Получено 3 матчей с BetBoom
[2025-11-09 14:25:31] INFO: Данные сохранены (3 матчей)
[2025-11-09 14:25:32] INFO: Запускаем analyze_and_send_telegram.py...
[2025-11-09 14:25:33] SUCCESS: Анализ и отправка завершены успешно!
```

---

## ❌ Возможные ошибки и решения

### Ошибка: "Connection refused"
```
❌ Ошибка подключения: [Errno 10061]
```
**Решение:** Проверить интернет и доступ к Telegram API

### Ошибка: "Invalid token"
```
❌ Ошибка Telegram: {'ok': False, 'error_code': 401, 'description': 'Unauthorized'}
```
**Решение:** Проверить BOT_TOKEN в конфиге

### Ошибка: "Not a channel"
```
❌ Ошибка Telegram: {'ok': False, 'error_code': 400, 'description': 'Bad Request: chat not found'}
```
**Решение:** Убедиться что CHANNEL_ID = '@TrueLiveBet' правильный

---

## 🎛️ Тестирование

### 1️⃣ Тест отправки (с тестовыми данными)
```bash
python analyze_and_send_telegram.py
```

### 2️⃣ Тест с конкретными матчами
```python
# Создать скрипт test_analysis.py
from analyze_and_send_telegram import main

test_matches = [
    {
        'team1': 'Пример 1',
        'team2': 'Пример 2',
        'score': '2-1',
        'league': 'Лига примеров',
        'time': '1Т, 30 мин',
        'coef_p1': 1.5,
        'coef_p2': 2.5
    }
]

main(matches_data=test_matches)
```

### 3️⃣ Тест с обработчиком AHK
```bash
# Запустить обработчик в режиме мониторинга
python ahk_trigger_handler.py monitor

# Ввести: 🎯F (или просто "f")
# Должен запуститься анализ
```

---

## 🔗 Связанные файлы

- **`analyzer_with_justification.py`** - основная логика анализа
- **`telegram_simple.py`** - простая отправка (альтернатива)
- **`send_fixed_analysis.py`** - улучшенная отправка (альтернатива)
- **`config.json`** - конфигурация проекта
- **`cursor_autosend.ahk`** - AutoHotkey скрипт для автоматического запуска

---

## 📚 Дополнительные команды

```bash
# Показать справку
python ahk_trigger_handler.py help

# Запустить анализ (одноразово)
python ahk_trigger_handler.py run

# Мониторить сигналы от AHK (фоновый режим)
python ahk_trigger_handler.py monitor

# Запустить тесты
python -m pytest test_telegram_integration.py
```

---

## ✨ Готово к использованию!

Все компоненты интеграции с Telegram готовы:

✅ Анализ матчей  
✅ Форматирование сообщений  
✅ Отправка в @TrueLiveBet  
✅ Обработка сигналов от AutoHotkey  
✅ Логирование событий  

Можешь запустить сейчас:
```bash
python analyze_and_send_telegram.py
```

