# 🤖 ПОЛНОСТЬЮ АВТОНОМНАЯ СИСТЕМА АНАЛИЗА BETBOOM

## 🎯 Схема Работы

```
┌─────────────────────────────────────────────────────────────┐
│  ПОЛНОСТЬЮ АВТОНОМНАЯ СИСТЕМА (БЕЗ УЧАСТИЯ ВИКТОРА)         │
└─────────────────────────────────────────────────────────────┘

1️⃣  АВТОКЛИКЕР (working_autoclicker.py)
    │
    ├─→ ⏰ Каждые 45 минут (9:00-23:30 МСК)
    ├─→ 🖱️ Кликает в Cursor Chat (координаты: 2026, 1361)
    ├─→ 📝 Вставляет запрос на анализ
    └─→ ⏎ Отправляет Enter
    
         │
         ▼
    
2️⃣  ИИ-АССИСТЕНТ (автоматически в Cursor)
    │
    ├─→ 📨 Получает запрос в чат
    ├─→ 🌐 Открывает BetBoom через Browser MCP
    ├─→ 📊 Анализирует матчи (футбол, теннис, гандбол)
    ├─→ 🎯 Применяет двухуровневую систему отбора
    ├─→ 📝 Сохраняет в current_live_analysis_mcp.txt
    └─→ 🚀 Запускает send_fixed_analysis.py
    
         │
         ▼
    
3️⃣  ОТПРАВЩИК (send_fixed_analysis.py)
    │
    ├─→ 📖 Читает current_live_analysis_mcp.txt
    ├─→ 🤖 Использует Telegram Bot API
    ├─→ 📱 Отправляет в канал @TrueLiveBet
    └─→ ✅ Логирует результат
    
         │
         ▼
    
4️⃣  ПОДПИСЧИКИ КАНАЛА
    └─→ 💰 Получают рекомендации для ставок
```

---

## 📦 НЕОБХОДИМЫЕ ФАЙЛЫ

### КРИТИЧЕСКИ ВАЖНЫЕ (3 файла):

```
1. working_autoclicker.py       ← ГЛАВНЫЙ: отправляет запросы каждые 45 мин
2. send_fixed_analysis.py       ← Отправка результатов в Telegram  
3. requirements.txt             ← Зависимости Python
```

### ОПЦИОНАЛЬНЫЕ (для тестирования):

```
4. create_test_trigger.py       ← Тестовый триггер (для файловой системы)
5. check_analysis_triggers.py   ← Проверка триггеров (для файловой системы)
```

### ДОКУМЕНТАЦИЯ:

```
6. AUTONOMOUS_SYSTEM_GUIDE.md   ← Эта инструкция
7. ALGORITHM_MATCH_SELECTION.md ← Алгоритм отбора матчей
8. WORKING_METHOD.md            ← Методология работы
```

---

## 🚀 БЫСТРЫЙ СТАРТ НА НОВОМ КОМПЬЮТЕРЕ

### Шаг 1: Установка зависимостей

```bash
# Windows
pip install pyautogui pyperclip schedule requests

# Linux/Mac
pip3 install pyautogui pyperclip schedule requests
```

### Шаг 2: Проверка координат

**ВАЖНО:** Координаты (2026, 1361) работают на текущем компьютере Виктора.

На новом компьютере нужно:

1. Открыть Cursor
2. Открыть этот чат
3. Узнать координаты поля ввода:

```python
# Запустить этот код для определения координат:
import pyautogui
import time

print("Наведи мышь на поле ввода чата через 5 секунд...")
time.sleep(5)
x, y = pyautogui.position()
print(f"Координаты: ({x}, {y})")
```

4. Записать координаты в `working_autoclicker.py`:

```python
# Строки 27-28
CHAT_X = 2026  # ← ЗАМЕНИ на новые координаты
CHAT_Y = 1361  # ← ЗАМЕНИ на новые координаты
```

### Шаг 3: Настройка Browser MCP

1. Убедиться, что Browser MCP установлен в Cursor
2. Открыть вкладку BetBoom в браузере
3. Кликнуть на иконку Browser MCP → "Connect"

### Шаг 4: Проверка Telegram

```python
# Убедиться что токен и канал правильные в send_fixed_analysis.py:
BOT_TOKEN = '7824400107:AAGZqPdS0E0N3HsYpD8TW9m8c-bapFd-RHk'
CHANNEL_ID = '@TrueLiveBet'
```

### Шаг 5: Тестовый запуск

```bash
# Windows
start_working_autoclicker.bat

# Linux/Mac
python3 working_autoclicker.py
```

### Шаг 6: Автозапуск при загрузке системы

#### Windows:

1. Нажми `Win+R`
2. Введи `shell:startup`
3. Создай ярлык на `start_working_autoclicker.bat`
4. Готово! Будет запускаться автоматически

#### Linux (systemd):

```bash
# Создать файл /etc/systemd/system/betboom-autoclicker.service
[Unit]
Description=BetBoom Autoclicker
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/betboom_analyzer
ExecStart=/usr/bin/python3 /home/your_username/betboom_analyzer/working_autoclicker.py
Restart=always

[Install]
WantedBy=multi-user.target

# Активировать
sudo systemctl enable betboom-autoclicker.service
sudo systemctl start betboom-autoclicker.service
```

---

## ⚙️ НАСТРОЙКИ И КОНФИГУРАЦИЯ

### Изменение интервала отправки

В файле `working_autoclicker.py`, строка 113:

```python
def setup_schedule():
    # Текущие настройки: каждые 45 минут с 9:00 до 23:30
    
    # Чтобы изменить на 30 минут:
    times = []
    for hour in range(9, 24):
        times.append(f"{hour:02d}:00")
        times.append(f"{hour:02d}:30")  # Каждые 30 мин
    
    # Чтобы изменить на 60 минут:
    times = []
    for hour in range(9, 24):
        times.append(f"{hour:02d}:00")  # Каждый час
```

### Изменение рабочих часов

В файле `working_autoclicker.py`, строки 37-48:

```python
def is_working_hours():
    moscow_time = get_moscow_time()
    hour = moscow_time.hour
    
    # Изменить 9 на нужный час начала
    if hour < 9:
        return False
    
    # Изменить 23 на нужный час окончания
    if hour > 23:
        return False
```

### Текст запроса

В файле `working_autoclicker.py`, строки 60-70:

```python
request_text = f"""🎯 АВТОМАТИЧЕСКИЙ ЗАПРОС НА АНАЛИЗ BETBOOM - {current_time.strftime('%H:%M')} МСК

Проверь актуальные матчи на BetBoom:
- Футбол: https://betboom.ru/sport/football?period=all&type=live
- Теннис: https://betboom.ru/sport/tennis?period=all&type=live  
- Гандбол: https://betboom.ru/sport/handball?period=all&type=live

Проведи анализ по системе (включая гандбольные тоталы!) и отправь результаты в канал @TrueLiveBet

Время запроса: {current_time.strftime('%d.%m.%Y %H:%M:%S')} МСК"""
```

---

## 🔧 УСТРАНЕНИЕ НЕПОЛАДОК

### Проблема: Автокликер не кликает в нужное место

**Решение:**
1. Определить новые координаты (см. Шаг 2)
2. Обновить CHAT_X и CHAT_Y в `working_autoclicker.py`
3. Перезапустить автокликер

### Проблема: ИИ не получает запросы

**Проверить:**
1. Окно Cursor открыто и активно
2. Поле ввода чата видно на экране
3. Координаты правильные
4. Логи в `working_autoclicker.log`

### Проблема: Browser MCP не работает

**Решение:**
1. Переподключить Browser MCP (иконка → Connect)
2. Перезапустить Cursor
3. Проверить, что вкладка BetBoom открыта

### Проблема: Сообщения не приходят в Telegram

**Проверить:**
1. Токен бота правильный
2. Канал @TrueLiveBet существует
3. Бот добавлен в канал как администратор
4. Файл `current_live_analysis_mcp.txt` создается

### Проблема: Ошибки в логах

```bash
# Проверить логи
tail -f working_autoclicker.log
```

---

## 📊 МОНИТОРИНГ СИСТЕМЫ

### Проверка работы автокликера

```bash
# Windows
type working_autoclicker.log

# Linux/Mac
tail -50 working_autoclicker.log
```

**Что искать в логах:**
- ✅ `Запрос отправлен!` - автокликер работает
- ❌ `Ошибка при отправке` - проблема с координатами
- ⏰ `Вне рабочих часов` - нормально, если вне 9:00-23:30

### Проверка отправки в Telegram

**Зайти в канал @TrueLiveBet:**
- Должны приходить сообщения каждые 45 минут
- Формат: заголовок + матчи по категориям + дисклеймер

### Статистика работы

```python
# Подсчет отправленных запросов в день
# При интервале 45 минут: (23:30 - 9:00) / 0.75 = ~19-20 запросов/день
```

---

## 🎯 ЧЕКЛИСТ ПОСЛЕ УСТАНОВКИ

```
□ Python установлен (3.8+)
□ Зависимости установлены: pip install pyautogui pyperclip schedule requests
□ Cursor открыт с этим чатом
□ Координаты поля ввода определены и записаны
□ Browser MCP установлен и подключен
□ Telegram токен и канал проверены
□ Тестовый запуск прошел успешно
□ Сообщение пришло в @TrueLiveBet
□ Автозапуск настроен (startup/systemd)
□ Логи пишутся корректно
□ Система работает автономно
```

---

## ⚠️ ВАЖНЫЕ НАПОМИНАНИЯ

### ДЛЯ ВИКТОРА:

1. **НЕ ЗАКРЫВАЙ Cursor** - автокликер должен видеть окно
2. **НЕ МЕНЯЙ координаты** (2026, 1361) - они работают идеально [[memory:9157063]]
3. **НЕ ВЫКЛЮЧАЙ компьютер** - система должна работать 24/7
4. Если переезжаешь на сервер - проверь координаты заново

### ДЛЯ ИИ-АССИСТЕНТА:

1. Всегда анализировать матчи ТОЛЬКО с указанных ссылок BetBoom
2. Обязательно проверять гандбольные тоталы
3. Сохранять результат в `current_live_analysis_mcp.txt`
4. Запускать `send_fixed_analysis.py` после анализа
5. Указывать полные названия обеих команд

---

## 🎉 СИСТЕМА ГОТОВА!

Теперь всё работает **ПОЛНОСТЬЮ АВТОНОМНО**:

✅ Автокликер отправляет запросы каждые 45 минут  
✅ ИИ автоматически анализирует через Browser MCP  
✅ Результаты автоматически отправляются в @TrueLiveBet  
✅ Виктор может не быть за компьютером  
✅ Система работает 24/7 без вмешательства  

---

**Последнее обновление:** 03.10.2025  
**Статус:** ✅ ПОЛНОСТЬЮ РАБОЧАЯ СИСТЕМА

