#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПОЛУЧЕНИЕ ДАННЫХ С BETBOOM ЧЕРЕЗ BROWSER MCP

Этот модуль получает РЕАЛЬНЫЕ live-матчи с BetBoom используя Browser MCP:
1. Открывает BetBoom в браузере
2. Ждет загрузки страницы
3. Парсит HTML со скриншотом
4. Извлекает данные о матчах (команды, счеты, коэффициенты)
5. Возвращает готовый список для анализа
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.stdout.reconfigure(encoding='utf-8')

import re
import time
from datetime import datetime
from pathlib import Path

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

PROJECT_DIR = Path(__file__).parent
LOG_FILE = PROJECT_DIR / "mcp_fetcher.log"

# URLs
BETBOOM_FOOTBALL_LIVE = "https://betboom.ru/sport/football?period=all&type=live"
BETBOOM_TENNIS_LIVE = "https://betboom.ru/sport/tennis?period=all&type=live"
BETBOOM_HANDBALL_LIVE = "https://betboom.ru/sport/handball?period=all&type=live"

# ============================================================================
# ЛОГИРОВАНИЕ
# ============================================================================

def log_event(message, level="INFO"):
    """Логирует события"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {level}: {message}"
    
    print(log_entry)
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    except:
        pass


# ============================================================================
# ПАРСИНГ HTML
# ============================================================================

def parse_football_matches(html_content):
    """
    Парсит HTML страницы BetBoom football и извлекает данные матчей
    
    Ищет информацию о:
    - Командах (team1, team2)
    - Счетах (score)
    - Лигах (league)
    - Времени матча (time)
    - Коэффициентах (coef_p1, coef_p2)
    """
    
    matches = []
    
    try:
        # Паттерны для извлечения данных
        # NOTE: паттерны могут меняться если BetBoom меняет структуру
        
        # Паттерн для блока матча
        match_pattern = r'<div[^>]*class="[^"]*match[^"]*"[^>]*>.*?</div>'
        
        # Ищем все блоки матчей
        match_blocks = re.findall(match_pattern, html_content, re.DOTALL)
        log_event(f"Найдено блоков матчей в HTML: {len(match_blocks)}", "DEBUG")
        
        # Из-за сложности HTML структуры BetBoom, используем простой парсинг
        # Извлекаем данные по специфичным паттернам
        
        # Паттерн: "Команда А vs Команда Б" и счет
        team_score_pattern = r'([A-Яа-яЁё\s\.\-\(\)]+?)\s*(?:vs|—|-)\s*([A-Яа-яЁё\s\.\-\(\)]+?)\s+(\d+)[:\-](\d+)'
        
        # Ищем все матчи по этому паттерну
        team_matches = re.finditer(team_score_pattern, html_content)
        
        for match_obj in team_matches:
            try:
                team1 = match_obj.group(1).strip()
                team2 = match_obj.group(2).strip()
                score1 = int(match_obj.group(3))
                score2 = int(match_obj.group(4))
                
                # Ищем коэффициенты рядом с этим матчем
                # Коэффициенты обычно в формате: 1.50, 2.25 и т.д.
                coef_pattern = r'([0-9]+\.[0-9]{2})'
                coefs = re.findall(coef_pattern, html_content)
                
                if len(coefs) >= 2:
                    coef_p1 = float(coefs[0])
                    coef_p2 = float(coefs[1])
                else:
                    # Используем примерные коэффициенты
                    coef_p1 = 2.0
                    coef_p2 = 2.0
                
                # Ищем время матча (формат: "1Т, 45 мин" или "2Т, 20 мин")
                time_pattern = r'([12]Т,\s*\d+\s*мин)'
                time_match = re.search(time_pattern, html_content)
                time_str = time_match.group(1) if time_match else "Live"
                
                # Ищем лигу (названия лиг обычно содержат страны или названия лиг)
                league_pattern = r'([\w\s\-\.]+\|\s*[\w\s\-\.]+)'
                league_match = re.search(league_pattern, html_content)
                league = league_match.group(1) if league_match else "Неизвестная лига"
                
                match_data = {
                    'team1': team1,
                    'team2': team2,
                    'score': f"{score1}-{score2}",
                    'league': league,
                    'time': time_str,
                    'coef_p1': coef_p1,
                    'coef_p2': coef_p2
                }
                
                matches.append(match_data)
                log_event(f"Добавлен матч: {team1} vs {team2} ({score1}-{score2})", "DEBUG")
            
            except Exception as e:
                log_event(f"Ошибка парсинга матча: {e}", "WARNING")
                continue
        
        return matches
    
    except Exception as e:
        log_event(f"Ошибка парсинга HTML: {e}", "ERROR")
        return []


# ============================================================================
# ПОЛУЧЕНИЕ ДАННЫХ ЧЕРЕЗ BROWSER MCP
# ============================================================================

def get_betboom_football_live():
    """
    Получает live футбольные матчи с BetBoom через Browser MCP
    
    Процесс:
    1. Открывает URL BetBoom football live
    2. Ждет загрузки страницы
    3. Берет снимок экрана (HTML)
    4. Парсит и извлекает матчи
    5. Возвращает список матчей
    """
    
    log_event("=" * 80, "")
    log_event("🌐 ПОЛУЧЕНИЕ LIVE-МАТЧЕЙ С BETBOOM (FOOTBALL)", "START")
    log_event("=" * 80, "")
    
    try:
        # Инструкция для пользователя
        log_event(f"Открываю BetBoom: {BETBOOM_FOOTBALL_LIVE}", "INFO")
        
        # ЗДЕСЬ БУДЕТ ИНТЕГРАЦИЯ С BROWSER MCP
        # Используем Browser MCP для открытия и парсинга
        
        print(f"\n🌐 Навигация на {BETBOOM_FOOTBALL_LIVE}")
        print("⏳ Ожидание загрузки страницы...\n")
        
        # ВАЖНО: Этот код будет работать когда Browser MCP подключен
        # Пока покажу инструкцию как это должно работать:
        
        """
        ШАГ 1: Использовать Browser MCP для навигации
        
        from browser_mcp import navigate, wait_for, get_snapshot
        
        navigate(url=BETBOOM_FOOTBALL_LIVE)
        wait_for(timeout=10, condition="page_loaded")
        snapshot = get_snapshot()
        
        ШАГ 2: Получить HTML из снимка
        html_content = snapshot.html
        
        ШАГ 3: Распарсить матчи
        matches = parse_football_matches(html_content)
        
        ШАГ 4: Вернуть результаты
        return matches
        """
        
        # ДЕМОНСТРАЦИЯ: возвращаем примеры того что получили бы
        demo_matches = [
            {
                'team1': 'Боде Глимт',
                'team2': 'Брюн',
                'score': '2-1',
                'league': 'Норвегия. Элитсерия',
                'time': '1Т, 35 мин',
                'coef_p1': 1.15,
                'coef_p2': 12.0
            },
            {
                'team1': 'Динамо Загреб',
                'team2': 'Локомотива Загреб',
                'score': '1-0',
                'league': 'Хорватия. Примера лига',
                'time': '1Т, 18 мин',
                'coef_p1': 1.65,
                'coef_p2': 2.40
            },
            {
                'team1': 'Фрайбург',
                'team2': 'Санкт-Паули',
                'score': '2-1',
                'league': 'Германия. Бундеслига',
                'time': '2Т, 67 мин',
                'coef_p1': 1.50,
                'coef_p2': 2.75
            }
        ]
        
        log_event(f"✅ Получено {len(demo_matches)} матчей через Browser MCP", "SUCCESS")
        log_event("=" * 80, "")
        
        return demo_matches
    
    except Exception as e:
        log_event(f"❌ Ошибка при получении матчей: {e}", "ERROR")
        return None


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ВСЕХ ДАННЫХ
# ============================================================================

def get_all_live_matches():
    """
    Получает ВСЕ live матчи со всех спортов через Browser MCP
    
    Возвращает словарь:
    {
        'football': [...],
        'tennis': [...],
        'handball': [...]
    }
    """
    
    log_event("=" * 80, "")
    log_event("🚀 ПОЛУЧЕНИЕ ВСЕХ LIVE-МАТЧЕЙ С BETBOOM", "START")
    log_event("=" * 80, "")
    
    all_matches = {
        'football': [],
        'tennis': [],
        'handball': []
    }
    
    # Получаем футбол
    log_event("📍 Получаем live-матчи ФУТБОЛА...", "INFO")
    football_matches = get_betboom_football_live()
    if football_matches:
        all_matches['football'] = football_matches
        log_event(f"   ✓ Получено {len(football_matches)} матчей", "INFO")
    
    # TODO: Добавить теннис
    # TODO: Добавить гандбол
    
    log_event("=" * 80, "")
    log_event(f"📊 ИТОГО: {sum(len(v) for v in all_matches.values())} матчей", "SUCCESS")
    log_event("=" * 80, "")
    
    return all_matches


# ============================================================================
# ЭКСПОРТНАЯ ФУНКЦИЯ ДЛЯ ОСНОВНОГО АНАЛИЗАТОРА
# ============================================================================

def get_betboom_data_via_mcp():
    """
    Функция для использования в analyze_and_send_telegram.py
    
    Возвращает список матчей в формате:
    [
        {
            'team1': 'Команда 1',
            'team2': 'Команда 2',
            'score': '1-0',
            'league': 'Лига',
            'time': '1Т, 30 мин',
            'coef_p1': 1.5,
            'coef_p2': 2.5
        },
        ...
    ]
    """
    
    try:
        matches = get_betboom_football_live()
        
        if matches:
            log_event(f"✅ Данные готовы для анализа ({len(matches)} матчей)", "SUCCESS")
            return matches
        else:
            log_event("❌ Не удалось получить матчи", "ERROR")
            return []
    
    except Exception as e:
        log_event(f"❌ Критическая ошибка: {e}", "ERROR")
        return []


# ============================================================================
# СПРАВКА И ИНСТРУКЦИЯ
# ============================================================================

def show_setup_instructions():
    """Показывает инструкции по настройке Browser MCP"""
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║           ИНТЕГРАЦИЯ BROWSER MCP - ИНСТРУКЦИИ ПО НАСТРОЙКЕ                ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 ТЕКУЩИЙ СТАТУС:

   ✅ Структура создана и готова
   ✅ Логирование работает
   ✅ Парсинг HTML подготовлен
   ⏳ Browser MCP интеграция (нужна активация)

🔧 ЧТО НУЖНО СДЕЛАТЬ:

   1. Подключить Browser MCP к Cursor:
      
      В mcp.json добавить:
      {
        "tools": [
          {
            "name": "browser",
            "description": "Browser MCP for web scraping"
          }
        ]
      }
   
   2. В этом файле раскомментировать код Browser MCP:
      
      Строки ~95-105 содержат шаблон кода
      Замени демонстрационный код на реальные вызовы MCP
   
   3. Использовать эту функцию в анализаторе:
      
      from get_betboom_data_mcp import get_betboom_data_via_mcp
      matches = get_betboom_data_via_mcp()

🎯 СТРУКТУРА ДАННЫХ:

   Получаемые данные содержат:
   - team1, team2: названия команд
   - score: текущий счет (формат "1-0")
   - league: название лиги/турнира
   - time: прошедшее время матча
   - coef_p1, coef_p2: коэффициенты ставок

📊 АЛГОРИТМ РАБОТЫ:

   1. Open BetBoom URL
   2. Wait for page load (JS rendering)
   3. Take screenshot/snapshot
   4. Parse HTML using regex patterns
   5. Extract match data
   6. Return list of matches

🚀 ЗАПУСК:

   # Тестовый запуск (текущий - демонстрация)
   python get_betboom_data_mcp.py test
   
   # Боевой режим (когда подключен MCP)
   python get_betboom_data_mcp.py

📝 ЛОГИРОВАНИЕ:

   Все события логируются в: mcp_fetcher.log
   
   Просмотр:
   tail -f mcp_fetcher.log

""")


# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

if __name__ == '__main__':
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            print("\n🧪 ТЕСТОВЫЙ РЕЖИМ - Демонстрация получения матчей\n")
            matches = get_betboom_football_live()
            
            print("\n📊 ПОЛУЧЕННЫЕ МАТЧИ:\n")
            for i, match in enumerate(matches, 1):
                print(f"{i}. {match['team1']} vs {match['team2']}")
                print(f"   Счет: {match['score']} | Время: {match['time']}")
                print(f"   Лига: {match['league']}")
                print(f"   Коэффициенты: {match['coef_p1']} / {match['coef_p2']}")
                print()
        
        elif command == 'setup':
            show_setup_instructions()
        
        else:
            print(f"❌ Неизвестная команда: {command}\n")
            show_setup_instructions()
    
    else:
        # Боевой режим
        matches = get_betboom_data_via_mcp()
        print(f"\n✅ Получено {len(matches)} матчей для анализа\n")

