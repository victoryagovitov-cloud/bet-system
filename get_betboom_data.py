#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПОЛУЧЕНИЕ ДАННЫХ С BETBOOM

Фасад для получения live-матчей с BetBoom
Может работать через:
1. Browser MCP (когда подключен)
2. Готовые данные из файла
3. Тестовые данные
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.stdout.reconfigure(encoding='utf-8')

import json
from pathlib import Path
from datetime import datetime

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

PROJECT_DIR = Path(__file__).parent
CACHE_FILE = PROJECT_DIR / "betboom_cache.json"


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def log(message, level="INFO"):
    """Простое логирование"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")


def cache_is_valid():
    """Проверяет, валидна ли кешированная информация (не старше 5 минут)"""
    if not CACHE_FILE.exists():
        return False
    
    file_age = datetime.now().timestamp() - CACHE_FILE.stat().st_mtime
    return file_age < 300  # 5 минут


def read_cache():
    """Читает матчи из кеша"""
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        log(f"Данные загружены из кеша ({len(data)} матчей)", "CACHE")
        return data
    
    except Exception as e:
        log(f"Ошибка чтения кеша: {e}", "ERROR")
        return None


def save_cache(matches_data):
    """Сохраняет матчи в кеш"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(matches_data, f, ensure_ascii=False, indent=2)
        
        log(f"Данные сохранены в кеш ({len(matches_data)} матчей)", "CACHE")
    
    except Exception as e:
        log(f"Ошибка сохранения кеша: {e}", "ERROR")


# ============================================================================
# ПОЛУЧЕНИЕ ДАННЫХ (ВАРИАНТ 1: Browser MCP)
# ============================================================================

def get_betboom_data_from_mcp():
    """
    Получает данные с BetBoom через Browser MCP
    
    Использует новый модуль get_betboom_data_mcp.py который:
    1. Открывает BetBoom в браузере через Browser MCP
    2. Ждет загрузки страницы
    3. Берет снимок экрана
    4. Парсит HTML и извлекает данные матчей
    5. Возвращает готовый список
    """
    
    log("Попытка получить данные через Browser MCP...", "INFO")
    
    try:
        # Импортируем функцию из нового модуля Browser MCP
        from get_betboom_data_mcp import get_betboom_data_via_mcp
        
        # Получаем данные через Browser MCP
        matches = get_betboom_data_via_mcp()
        
        if matches and len(matches) > 0:
            log(f"✅ Получено {len(matches)} матчей через Browser MCP", "SUCCESS")
            return matches
        else:
            log("⚠️  Browser MCP вернул пустой результат", "WARNING")
            return None
    
    except ImportError:
        log("⚠️  Модуль get_betboom_data_mcp.py не найден", "WARNING")
        return None
    
    except Exception as e:
        log(f"⚠️  Ошибка Browser MCP: {e}", "WARNING")
        return None


# ============================================================================
# ПОЛУЧЕНИЕ ДАННЫХ (ВАРИАНТ 2: API/Прямой парсинг)
# ============================================================================

def get_betboom_data_from_api():
    """
    Получает данные с BetBoom через прямой запрос
    (если BetBoom предоставляет JSON API)
    """
    
    log("Попытка получить данные через прямой запрос...", "INFO")
    
    try:
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Попытка получить JSON с матчами
        # ПРИМЕЧАНИЕ: URL может меняться, нужна актуализация
        url = "https://betboom.ru/sport/football?type=live&format=json"
        
        response = requests.get(url, verify=False, timeout=10)
        
        if response.status_code == 200:
            matches = response.json()
            log(f"Получено {len(matches)} матчей через API", "SUCCESS")
            return matches
        else:
            log(f"Ошибка API: {response.status_code}", "ERROR")
            return None
    
    except ImportError:
        log("requests не установлен", "WARNING")
        return None
    
    except Exception as e:
        log(f"Ошибка при получении данных: {e}", "ERROR")
        return None


# ============================================================================
# ПОЛУЧЕНИЕ ДАННЫХ (ВАРИАНТ 3: Готовые данные из файла)
# ============================================================================

def get_betboom_data_from_file():
    """
    Загружает готовые данные из файла
    Файл должен содержать JSON с матчами
    """
    
    data_file = PROJECT_DIR / "betboom_live_data.json"
    
    if not data_file.exists():
        log(f"Файл {data_file.name} не найден", "WARNING")
        return None
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            matches = json.load(f)
        
        log(f"Данные загружены из файла ({len(matches)} матчей)", "SUCCESS")
        return matches
    
    except Exception as e:
        log(f"Ошибка чтения файла: {e}", "ERROR")
        return None


# ============================================================================
# ПОЛУЧЕНИЕ ДАННЫХ (ВАРИАНТ 4: Тестовые данные)
# ============================================================================

def get_test_data():
    """
    Возвращает тестовые данные для демонстрации
    """
    
    log("Используются тестовые данные", "TEST")
    
    return [
        {
            'team1': 'АЗ Алкмаар',
            'team2': 'ПСВ Эйндховен',
            'score': '0-3',
            'league': 'Нидерланды. Эредивизи',
            'time': '1Т, 29 мин',
            'coef_p1': 60.0,
            'coef_p2': 1.03
        },
        {
            'team1': 'Боде Глимт',
            'team2': 'Брюн',
            'score': '1-0',
            'league': 'Норвегия. Элитсерия',
            'time': '1Т, 16 мин',
            'coef_p1': 1.03,
            'coef_p2': 45.0
        },
        {
            'team1': 'Сент Трюйден',
            'team2': 'Стандард Льеж',
            'score': '0-0',
            'league': 'Бельгия. 1-й дивизион',
            'time': '2Т, 57 мин',
            'coef_p1': 1.18,
            'coef_p2': 20.0
        },
        {
            'team1': 'Фрайбург',
            'team2': 'Санкт-Паули',
            'score': '2-1',
            'league': 'Германия. Бундеслига',
            'time': '2Т, 89 мин',
            'coef_p1': 1.50,
            'coef_p2': 4.5
        }
    ]


# ============================================================================
# ОСНОВНАЯ ФУНКЦИЯ - ПОЛУЧЕНИЕ ДАННЫХ
# ============================================================================

def get_betboom_data(use_cache=True, force_test=False):
    """
    Получает данные с BetBoom, пробуя разные источники
    
    Args:
        use_cache: использовать ли кешированные данные если они валидны
        force_test: использовать только тестовые данные
    
    Returns:
        список матчей или None
    """
    
    log("=" * 80, "")
    log("ПОЛУЧЕНИЕ ДАННЫХ С BETBOOM", "START")
    log("=" * 80, "")
    
    # Если нужны только тестовые данные
    if force_test:
        return get_test_data()
    
    # Стратегия получения данных:
    # 1. Проверяем кеш (если валиден)
    # 2. Пытаемся Browser MCP
    # 3. Пытаемся прямой запрос
    # 4. Пытаемся загрузить из файла
    # 5. Используем тестовые данные
    
    # 1. Кеш?
    if use_cache and cache_is_valid():
        data = read_cache()
        if data:
            return data
    
    # 2. Browser MCP?
    data = get_betboom_data_from_mcp()
    if data:
        save_cache(data)
        return data
    
    # 3. Прямой запрос?
    data = get_betboom_data_from_api()
    if data:
        save_cache(data)
        return data
    
    # 4. Из файла?
    data = get_betboom_data_from_file()
    if data:
        save_cache(data)
        return data
    
    # 5. Тестовые данные (fallback)
    log("Используем тестовые данные как fallback", "WARNING")
    return get_test_data()


# ============================================================================
# ИНФОРМАЦИЯ ПО ПОЛУЧЕНИЮ ДАННЫХ
# ============================================================================

def show_help():
    """Показывает справку по получению данных"""
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║            GET_BETBOOM_DATA - Получение данных                ║
╚════════════════════════════════════════════════════════════════╝

СТРАТЕГИЯ ПОЛУЧЕНИЯ:
  1. Кеш (если не старше 5 минут)
  2. Browser MCP (если подключен)
  3. Прямой API запрос (если доступен)
  4. Загрузка из файла betboom_live_data.json
  5. Тестовые данные (fallback)

ИСПОЛЬЗОВАНИЕ:

  from get_betboom_data import get_betboom_data
  
  # Получить данные с автоматической стратегией
  matches = get_betboom_data()
  
  # Получить тестовые данные
  matches = get_betboom_data(force_test=True)
  
  # Не использовать кеш
  matches = get_betboom_data(use_cache=False)

СОЗДАНИЕ СВОИХ ДАННЫХ:

  1. Создайте файл 'betboom_live_data.json' с содержимым:
  
    [
      {
        "team1": "Команда 1",
        "team2": "Команда 2",
        "score": "1-0",
        "league": "Лига",
        "time": "1Т, 20 мин",
        "coef_p1": 1.5,
        "coef_p2": 2.5
      }
    ]
  
  2. Скрипт автоматически загрузит эти данные

BROWSER MCP ИНТЕГРАЦИЯ:

  Когда Browser MCP будет подключен, добавить код:
  
  def get_betboom_data_from_mcp():
      # Использовать mcp_browsermcp_browser_navigate
      # Использовать mcp_browsermcp_browser_screenshot
      # Распарсить данные со скриншота
      # Вернуть matches
      pass
""")


if __name__ == '__main__':
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'help':
            show_help()
        
        elif command == 'test':
            print("\n📊 Тестовые данные:\n")
            data = get_betboom_data(force_test=True)
            for i, match in enumerate(data, 1):
                print(f"{i}. {match['team1']} vs {match['team2']} ({match['score']})")
        
        elif command == 'show':
            print("\n📊 Текущие данные с BetBoom:\n")
            data = get_betboom_data()
            for i, match in enumerate(data, 1):
                print(f"{i}. {match['team1']} vs {match['team2']} ({match['score']})")
        
        else:
            show_help()
    
    else:
        # По умолчанию просто получить и показать данные
        data = get_betboom_data()
        print(f"\n✅ Получено {len(data)} матчей\n")

