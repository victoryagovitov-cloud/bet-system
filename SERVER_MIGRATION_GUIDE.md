# 🚀 ИНСТРУКЦИЯ ДЛЯ ЗАПУСКА НА УДАЛЕННОМ СЕРВЕРЕ

## 📦 НЕОБХОДИМЫЕ ФАЙЛЫ ДЛЯ ПЕРЕНОСА

### КРИТИЧЕСКИ ВАЖНЫЕ (обязательны для работы):

```
📁 Корень проекта/
│
├── 🔧 ОСНОВНЫЕ СКРИПТЫ (3 файла)
│   ├── file_trigger_scheduler.py     ← Планировщик триггеров (45 мин)
│   ├── send_fixed_analysis.py        ← Отправка в Telegram
│   └── create_test_trigger.py        ← Создание тестового триггера
│
├── 🛠 ВСПОМОГАТЕЛЬНЫЕ (2 файла)
│   ├── check_analysis_triggers.py    ← Проверка триггеров
│   └── cleanup_old_files.py          ← Очистка старых файлов
│
├── 📚 ДОКУМЕНТАЦИЯ (4 файла)
│   ├── AUTOMATION_SYSTEM_FULL.md     ← Полная система автоматизации
│   ├── SERVER_MIGRATION_GUIDE.md     ← Эта инструкция
│   ├── ALGORITHM_MATCH_SELECTION.md  ← Алгоритм отбора матчей
│   └── WORKING_METHOD.md             ← Методология работы
│
├── 📄 КОНФИГУРАЦИЯ (2 файла)
│   ├── requirements.txt              ← Зависимости Python
│   └── config.json                   ← Настройки (если есть)
│
└── 📝 ДОПОЛНИТЕЛЬНАЯ ДОКУМЕНТАЦИЯ (опционально)
    ├── CHANNEL_DEVELOPMENT_STRATEGY.md
    ├── PREMIUM_STRATEGY_500_WEEK.md
    ├── MESSAGE_TEMPLATE_STANDARD.md
    └── другие .md файлы с стратегиями
```

**ИТОГО: ~15 основных файлов**

---

## 🔑 КЛЮЧЕВЫЕ ФАЙЛЫ И ИХ НАЗНАЧЕНИЕ

### 1️⃣ `file_trigger_scheduler.py` 
**Назначение:** Главный планировщик системы
- Создает файлы-триггеры каждые 45 минут
- Работает с 9:00 до 23:30 МСК
- Удаляет старые триггеры (>1 часа)

**Зависимости:**
```python
import schedule
import time
import logging
import os
from datetime import datetime, timezone, timedelta
```

---

### 2️⃣ `send_fixed_analysis.py`
**Назначение:** Отправка анализа в Telegram
- Читает `current_live_analysis_mcp.txt`
- Отправляет в канал @TrueLiveBet
- Без Markdown разметки (избежание искажений)

**Конфигурация внутри файла:**
```python
BOT_TOKEN = '7824400107:AAGZqPdS0E0N3HsYpD8TW9m8c-bapFd-RHk'
CHANNEL_ID = '@TrueLiveBet'
```

**Зависимости:**
```python
import requests
from datetime import datetime
import urllib3
```

---

### 3️⃣ `create_test_trigger.py`
**Назначение:** Создание тестового триггера для проверки
- Быстрое тестирование системы
- Создает файл `analysis_trigger_HH_MM.txt`

---

### 4️⃣ `check_analysis_triggers.py`
**Назначение:** Утилита для проверки триггеров
- Показать все триггеры
- Показать последний триггер
- Очистить старые триггеры

---

### 5️⃣ `current_live_analysis_mcp.txt`
**Назначение:** Результат анализа (создается ИИ)
- Генерируется автоматически после анализа BetBoom
- Читается `send_fixed_analysis.py`
- Формат: структурированное текстовое сообщение

---

## 🐧 УСТАНОВКА НА LINUX СЕРВЕР

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python 3 и pip
sudo apt install python3 python3-pip -y

# Проверка версии
python3 --version  # Должно быть 3.8+
```

### Шаг 2: Создание рабочей директории

```bash
# Создать папку проекта
mkdir -p ~/betboom_analyzer
cd ~/betboom_analyzer

# Установить права
chmod 755 ~/betboom_analyzer
```

### Шаг 3: Перенос файлов

**Вариант A: Через SCP (с локальной машины)**
```bash
scp -r D:/cursor/Backtothestart/* user@server_ip:~/betboom_analyzer/
```

**Вариант B: Через Git (рекомендуется)**
```bash
cd ~/betboom_analyzer
git init
git remote add origin YOUR_REPO_URL
git pull origin main
```

**Вариант C: Вручную через FileZilla/WinSCP**
- Подключиться к серверу
- Скопировать файлы из списка выше

### Шаг 4: Установка зависимостей

```bash
cd ~/betboom_analyzer

# Установка зависимостей
pip3 install -r requirements.txt

# Или вручную:
pip3 install schedule requests pyautogui pyperclip
```

### Шаг 5: Настройка часового пояса

```bash
# Установить московское время
sudo timedatectl set-timezone Europe/Moscow

# Проверить
date
```

---

## 🪟 УСТАНОВКА НА WINDOWS SERVER

### Шаг 1: Установка Python

1. Скачать Python 3.11+ с python.org
2. При установке отметить "Add Python to PATH"
3. Проверить: `python --version`

### Шаг 2: Создание папки проекта

```cmd
mkdir C:\betboom_analyzer
cd C:\betboom_analyzer
```

### Шаг 3: Перенос файлов

Скопировать все файлы из списка в `C:\betboom_analyzer\`

### Шаг 4: Установка зависимостей

```cmd
cd C:\betboom_analyzer
pip install -r requirements.txt
```

---

## ⚙️ НАСТРОЙКА АВТОЗАПУСКА

### Linux (systemd service)

**Создать сервис:**
```bash
sudo nano /etc/systemd/system/betboom-scheduler.service
```

**Содержимое:**
```ini
[Unit]
Description=BetBoom Live Analyzer Scheduler
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/betboom_analyzer
ExecStart=/usr/bin/python3 /home/YOUR_USERNAME/betboom_analyzer/file_trigger_scheduler.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Активация:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable betboom-scheduler
sudo systemctl start betboom-scheduler

# Проверка статуса
sudo systemctl status betboom-scheduler

# Просмотр логов
sudo journalctl -u betboom-scheduler -f
```

### Windows (Task Scheduler)

1. Открыть Task Scheduler
2. Create Task (Создать задачу)
3. **General:**
   - Name: BetBoom Scheduler
   - Run with highest privileges
4. **Triggers:**
   - At log on (при входе)
   - Или: At system startup (при запуске системы)
5. **Actions:**
   - Program: `C:\Python311\python.exe`
   - Arguments: `file_trigger_scheduler.py`
   - Start in: `C:\betboom_analyzer`
6. Save

---

## 🔄 WORKFLOW НА СЕРВЕРЕ

### Как это работает:

```
┌─────────────────────────────────────────────────┐
│  1. file_trigger_scheduler.py запущен на сервере │
│     (работает 24/7 в фоновом режиме)            │
└────────────────┬────────────────────────────────┘
                 │
                 │ Каждые 45 минут (9:00-23:30)
                 ↓
┌─────────────────────────────────────────────────┐
│  2. Создается analysis_trigger_HH_MM.txt        │
│     (файл с запросом на анализ)                 │
└────────────────┬────────────────────────────────┘
                 │
                 │ Виктор или ИИ видит триггер
                 ↓
┌─────────────────────────────────────────────────┐
│  3. ИИ (Cursor с Browser MCP) получает запрос   │
│     - Открывает BetBoom через браузер           │
│     - Анализирует матчи (футбол, теннис, гандбол)│
│     - Применяет критерии отбора (>80%)          │
└────────────────┬────────────────────────────────┘
                 │
                 │ Создает файл результатов
                 ↓
┌─────────────────────────────────────────────────┐
│  4. current_live_analysis_mcp.txt               │
│     (структурированный анализ матчей)           │
└────────────────┬────────────────────────────────┘
                 │
                 │ Виктор запускает отправку
                 ↓
┌─────────────────────────────────────────────────┐
│  5. python send_fixed_analysis.py               │
│     → Отправка в @TrueLiveBet                   │
└─────────────────────────────────────────────────┘
```

---

## 🤖 ИНТЕГРАЦИЯ С ИИ (КРИТИЧЕСКИ ВАЖНО!)

### ⚠️ ВАЖНОЕ ОГРАНИЧЕНИЕ:
**Browser MCP НЕВОЗМОЖНО запустить из Python!**

Он работает ТОЛЬКО через Cursor Chat:
- ИИ получает триггер
- ИИ использует Browser MCP через расширение
- ИИ анализирует BetBoom в реальном времени
- ИИ создает файл `current_live_analysis_mcp.txt`

### Решение на сервере:

**Вариант 1: Полуавтоматический (рекомендуется на старте)**
```
1. Сервер: file_trigger_scheduler.py работает
2. Сервер: создает триггеры
3. Виктор: видит триггер → копирует содержимое
4. Виктор: отправляет в Cursor Chat
5. ИИ: анализирует через Browser MCP
6. ИИ: создает current_live_analysis_mcp.txt
7. Сервер: автоматически отправляет в Telegram
```

**Вариант 2: Полная автоматизация (будущее)**
```
Разработать API-мост между сервером и Cursor:
- Сервер создает триггер
- API отправляет запрос в Cursor через webhook
- Cursor автоматически обрабатывает
- Результат возвращается на сервер
- Автоматическая отправка в Telegram

(Требует дополнительной разработки)
```

---

## 📋 ЧЕКЛИСТ ПОСЛЕ МИГРАЦИИ

### Проверка окружения:
- [ ] Python 3.8+ установлен
- [ ] pip работает
- [ ] Часовой пояс: Europe/Moscow
- [ ] Все зависимости установлены
- [ ] requirements.txt проверен

### Проверка файлов:
- [ ] file_trigger_scheduler.py на месте
- [ ] send_fixed_analysis.py на месте
- [ ] create_test_trigger.py на месте
- [ ] check_analysis_triggers.py на месте
- [ ] AUTOMATION_SYSTEM_FULL.md на месте

### Проверка конфигурации:
- [ ] BOT_TOKEN проверен в send_fixed_analysis.py
- [ ] CHANNEL_ID проверен (@TrueLiveBet)
- [ ] Права на запись в папку проекта
- [ ] Права на создание файлов

### Тестирование:
- [ ] Создать тестовый триггер: `python3 create_test_trigger.py`
- [ ] Проверить триггер: `python3 check_analysis_triggers.py`
- [ ] Запустить планировщик: `python3 file_trigger_scheduler.py`
- [ ] Проверить создание триггеров (подождать до рабочих часов)
- [ ] Провести тестовый анализ через ИИ
- [ ] Отправить в Telegram: `python3 send_fixed_analysis.py`
- [ ] Проверить сообщение в канале @TrueLiveBet

### Автозапуск:
- [ ] systemd service создан (Linux)
- [ ] systemd service включен
- [ ] systemd service запущен
- [ ] Task Scheduler настроен (Windows)
- [ ] Логи работают
- [ ] Перезагрузка сервера → планировщик запустился

---

## 🔍 МОНИТОРИНГ И ЛОГИ

### Где смотреть логи:

**Linux:**
```bash
# Логи планировщика
sudo journalctl -u betboom-scheduler -f

# Последние 100 строк
sudo journalctl -u betboom-scheduler -n 100

# Логи с определенного времени
sudo journalctl -u betboom-scheduler --since "2025-10-04 09:00"
```

**Windows:**
```cmd
# Просмотр лог-файла (если создается)
type file_trigger_scheduler.log

# Или открыть в Notepad
notepad file_trigger_scheduler.log
```

### Что проверять:

✅ **Планировщик работает:**
```
2025-10-04 09:00:04 - INFO - 📁 Создан триггер: analysis_trigger_09_00.txt
2025-10-04 09:45:04 - INFO - 📁 Создан триггер: analysis_trigger_09_45.txt
```

✅ **Триггеры создаются:**
```bash
ls -la analysis_trigger_*.txt
```

✅ **Отправка работает:**
```
MCP ANALIZ OTPRAVLEN V @TrueLiveBet!
Message ID: XXX
```

---

## 🚨 УСТРАНЕНИЕ НЕПОЛАДОК

### Проблема: Планировщик не запускается

**Проверка:**
```bash
# Linux
python3 file_trigger_scheduler.py

# Windows
python file_trigger_scheduler.py
```

**Ошибки:**
- `ModuleNotFoundError: No module named 'schedule'` → `pip3 install schedule`
- Permission denied → `chmod +x file_trigger_scheduler.py`

### Проблема: Триггеры не создаются

**Причины:**
1. Вне рабочих часов (9:00-23:30 МСК)
2. Неправильный часовой пояс
3. Нет прав на запись

**Решение:**
```bash
# Проверить время
date

# Проверить часовой пояс
timedatectl

# Проверить права
ls -la analysis_trigger_*.txt
```

### Проблема: Отправка не работает

**Проверка:**
```bash
# Проверить файл анализа
cat current_live_analysis_mcp.txt

# Проверить токен бота
grep BOT_TOKEN send_fixed_analysis.py

# Тест отправки
python3 send_fixed_analysis.py
```

**Ошибки:**
- 401 Unauthorized → неверный BOT_TOKEN
- 403 Forbidden → бот не админ в канале
- 404 Not Found → неверный CHANNEL_ID

---

## 📞 КОНТАКТЫ И ПОДДЕРЖКА

### Важные параметры для проверки:

```python
# Telegram Bot
BOT_TOKEN = '7824400107:AAGZqPdS0E0N3HsYpD8TW9m8c-bapFd-RHk'
CHANNEL_ID = '@TrueLiveBet'

# Расписание
WORKING_HOURS = '9:00-23:30 MSK'
INTERVAL = '45 minutes'
DAILY_RUNS = 19

# BetBoom URLs
FOOTBALL_URL = 'https://betboom.ru/sport/football?period=all&type=live'
TENNIS_URL = 'https://betboom.ru/sport/tennis?period=all&type=live'
HANDBALL_URL = 'https://betboom.ru/sport/handball?period=all&type=live'
```

---

## ✅ ФИНАЛЬНЫЙ ЧЕКЛИСТ

После настройки на сервере проверь:

- [x] Python установлен и работает
- [x] Все файлы скопированы
- [x] Зависимости установлены
- [x] Часовой пояс: Moscow
- [x] Тестовый триггер создается
- [x] Планировщик запускается
- [x] Триггеры создаются каждые 45 мин
- [x] ИИ может получать триггеры
- [x] Browser MCP подключен
- [x] Анализ проходит успешно
- [x] current_live_analysis_mcp.txt создается
- [x] Отправка в Telegram работает
- [x] Сообщения приходят в @TrueLiveBet
- [x] Автозапуск настроен
- [x] Логи читаются
- [x] Система работает автономно

---

## 🎯 КРАТКАЯ ПАМЯТКА ДЛЯ ИИ

### При получении триггера делай:

1. **Прочитать триггер** → понять запрос
2. **Browser MCP** → загрузить футбол, теннис, гандбол
3. **Анализ** → применить критерии (>80%)
4. **Гандбол** → ОБЯЗАТЕЛЬНО проверить тоталы (формула)
5. **Сформировать** → структурированное сообщение
6. **Сохранить** → `current_live_analysis_mcp.txt`
7. **Сообщить** → "Анализ готов, запускай send_fixed_analysis.py"

### Критерии анализа:

- ⚽ **Футбол:** неничейный счет + фаворит ведет + времени мало
- 🎾 **Теннис:** выиграл 1-й сет + ведет во 2-м
- 🤾 **Гандбол:** исходы + ТОТАЛЫ (формула расчета)

### Формула тотала (гандбол):
```
Прогноз = (текущий_счет ÷ прошедшие_минуты) × оставшиеся_минуты + текущий_счет
М = Прогноз + 2-3
Б = Прогноз - 2-3
```

---

**Система готова к работе на сервере! 🚀**

