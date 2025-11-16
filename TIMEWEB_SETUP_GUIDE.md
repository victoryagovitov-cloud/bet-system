# 🚀 РУКОВОДСТВО ПО НАСТРОЙКЕ TIMEWEB СЕРВЕРА

## 📋 ЧЕК-ЛИСТ ЗАКАЗА СЕРВЕРА

### При заказе VPS выбрать:
- [x] **ОС:** Ubuntu 20.04 LTS
- [x] **Конфигурация:** VPS SSD-3 (4 ядра, 8GB RAM, 50GB SSD)
- [x] **Дата-центр:** Москва (для лучшего пинга)
- [x] **SSH-ключи:** Создать новый ключ
- [x] **Firewall:** Оставить стандартные настройки

---

## 🔧 ПЕРВИЧНАЯ НАСТРОЙКА СЕРВЕРА

### 1. Подключение к серверу
```bash
# Получить IP и данные доступа в панели Timeweb
ssh root@YOUR_SERVER_IP

# Обновление системы
apt update && apt upgrade -y
```

### 2. Создание пользователя
```bash
# Создание пользователя для проекта
adduser betboom
usermod -aG sudo betboom

# Настройка SSH для пользователя
mkdir /home/betboom/.ssh
cp /root/.ssh/authorized_keys /home/betboom/.ssh/
chown -R betboom:betboom /home/betboom/.ssh
chmod 700 /home/betboom/.ssh
chmod 600 /home/betboom/.ssh/authorized_keys
```

### 3. Установка базового ПО
```bash
# Python и зависимости
apt install python3.10 python3.10-venv python3-pip -y
apt install build-essential python3-dev -y

# Для Browser MCP
apt install chromium-browser xvfb fonts-liberation -y
apt install xauth x11-apps -y

# Дополнительные утилиты
apt install htop curl wget git nano -y
```

---

## 🐍 РАЗВЕРТЫВАНИЕ ПРОЕКТА

### 1. Подготовка окружения
```bash
# Переключение на пользователя betboom
su - betboom

# Создание директории проекта
mkdir ~/betboom-analyzer
cd ~/betboom-analyzer

# Виртуальное окружение Python
python3.10 -m venv venv
source venv/bin/activate

# Обновление pip
pip install --upgrade pip
```

### 2. Перенос файлов проекта
```bash
# Вариант 1: Через SCP с локального ПК
# На локальном ПК выполнить:
scp -r D:\cursor\Backtothestart/* betboom@YOUR_SERVER_IP:~/betboom-analyzer/

# Вариант 2: Через Git (если есть репозиторий)
git clone https://github.com/username/betboom-analyzer.git
cd betboom-analyzer

# Вариант 3: Ручная загрузка через панель Timeweb
# Использовать файловый менеджер в панели управления
```

### 3. Установка зависимостей
```bash
# Активация окружения
source venv/bin/activate

# Установка основных зависимостей
pip install aiohttp>=3.8.0
pip install schedule>=1.2.0
pip install requests>=2.28.0
pip install urllib3>=1.26.0
pip install pyautogui>=0.9.54
pip install pillow>=9.0.0
pip install python-dateutil>=2.8.0

# Или из файла requirements.txt (если есть)
pip install -r requirements.txt
```

---

## ⚙️ НАСТРОЙКА АВТОЗАПУСКА

### 1. Создание systemd сервиса
```bash
# Создание файла сервиса (от root)
sudo nano /etc/systemd/system/betboom-analyzer.service
```

**Содержимое файла сервиса:**
```ini
[Unit]
Description=BetBoom Live Analyzer
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=betboom
Group=betboom
WorkingDirectory=/home/betboom/betboom-analyzer
Environment=DISPLAY=:99
Environment=PYTHONPATH=/home/betboom/betboom-analyzer
ExecStartPre=/bin/bash -c 'Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp > /dev/null 2>&1 &'
ExecStart=/home/betboom/betboom-analyzer/venv/bin/python fixed_full_cycle_scheduler.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 2. Активация сервиса
```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable betboom-analyzer

# Запуск сервиса
sudo systemctl start betboom-analyzer

# Проверка статуса
sudo systemctl status betboom-analyzer
```

---

## 📊 МОНИТОРИНГ И ЛОГИ

### 1. Просмотр логов
```bash
# Логи systemd
sudo journalctl -u betboom-analyzer -f

# Логи приложения
tail -f ~/betboom-analyzer/fixed_full_cycle_scheduler.log

# Логи за последний час
sudo journalctl -u betboom-analyzer --since "1 hour ago"
```

### 2. Мониторинг ресурсов
```bash
# Использование CPU/RAM
htop

# Статус сервиса
systemctl status betboom-analyzer

# Проверка процессов
ps aux | grep python
ps aux | grep chromium
```

### 3. Управление сервисом
```bash
# Остановка
sudo systemctl stop betboom-analyzer

# Запуск
sudo systemctl start betboom-analyzer

# Перезапуск
sudo systemctl restart betboom-analyzer

# Отключение автозапуска
sudo systemctl disable betboom-analyzer
```

---

## 🔒 БЕЗОПАСНОСТЬ

### 1. Настройка Firewall
```bash
# Установка ufw
sudo apt install ufw -y

# Базовые правила
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Разрешение SSH
sudo ufw allow ssh

# Разрешение HTTPS (для API запросов)
sudo ufw allow out 443
sudo ufw allow out 80

# Активация firewall
sudo ufw enable
```

### 2. Обновления безопасности
```bash
# Автоматические обновления
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure unattended-upgrades

# Ручное обновление
sudo apt update && sudo apt upgrade -y
```

---

## 🧪 ТЕСТИРОВАНИЕ

### 1. Проверка окружения
```bash
# Проверка Python
python3.10 --version
which python3.10

# Проверка виртуального окружения
source ~/betboom-analyzer/venv/bin/activate
pip list

# Проверка Chromium
chromium-browser --version
```

### 2. Тестовый запуск
```bash
# Активация окружения
cd ~/betboom-analyzer
source venv/bin/activate

# Тестовый запуск планировщика
python fixed_full_cycle_scheduler.py

# Тест отправки в Telegram
python send_fixed_analysis.py
```

### 3. Проверка Browser MCP
```bash
# Запуск виртуального дисплея
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Тест браузера
chromium-browser --headless --no-sandbox --dump-dom https://betboom.ru
```

---

## 🎯 ФИНАЛЬНАЯ ПРОВЕРКА

### Чек-лист готовности:
- [ ] Сервер настроен и обновлен
- [ ] Python 3.10 и venv работают
- [ ] Все зависимости установлены
- [ ] Browser MCP функционирует
- [ ] Systemd сервис создан и активен
- [ ] Логи пишутся корректно
- [ ] Telegram API работает
- [ ] Планировщик запускается по расписанию
- [ ] Firewall настроен
- [ ] Мониторинг работает

### Команды для финальной проверки:
```bash
# Статус всех компонентов
sudo systemctl status betboom-analyzer
ps aux | grep python
tail -n 20 ~/betboom-analyzer/fixed_full_cycle_scheduler.log

# Тест сетевых подключений
curl -I https://betboom.ru
curl -I https://api.telegram.org

# Проверка ресурсов
df -h
free -h
```

---

## 📞 ПОДДЕРЖКА

### В случае проблем:
1. **Проверить логи:** `journalctl -u betboom-analyzer -f`
2. **Перезапустить сервис:** `sudo systemctl restart betboom-analyzer`
3. **Проверить сеть:** `ping betboom.ru`
4. **Освободить место:** `sudo apt autoremove && sudo apt autoclean`

### Контакты Timeweb поддержки:
- **Телефон:** 8 (800) 700-06-08
- **Чат:** В панели управления
- **Email:** support@timeweb.ru

---

## 🚀 ГОТОВО!

После выполнения всех шагов система будет работать автономно:
- ⏰ Каждые 30 минут с 8:00 до 23:30 МСК
- 🧠 Экспертный анализ через Browser MCP
- 📱 Автоматическая отправка в @TrueLiveBet
- 📊 Полное логирование всех операций
- 🔄 Автоматический перезапуск при сбоях

**СИСТЕМА ГОТОВА К ПОЛНОСТЬЮ АВТОНОМНОЙ РАБОТЕ!** 🎉
