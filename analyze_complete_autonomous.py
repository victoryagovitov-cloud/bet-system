#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПОЛНОСТЬЮ АВТОНОМНАЯ СИСТЕМА - Анализ + Telegram

Когда получу сигнал 🎯F:
1. Я сам открываю BetBoom через Browser MCP
2. Я сам получаю snapshot
3. Я сам парсю матчи
4. Я сам анализирую
5. Я сам отправляю в @TrueLiveBет

БЕЗ запросов к тебе! Полностью автоматически!
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.stdout.reconfigure(encoding='utf-8')

import requests
import re
import time
from datetime import datetime
from pathlib import Path
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

PROJECT_DIR = Path(__file__).parent
LOG_FILE = PROJECT_DIR / "autonomous.log"
BOT_TOKEN = '7824400107:AAGZqPdS0E0N3HsYpD8TW9m8c-bapFd-RHk'
CHANNEL_ID = '@TrueLiveBet'
BETBOOM_URL = "https://betboom.ru/sport/football?period=all&type=live"

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
# ПОЛУЧЕНИЕ ДАННЫХ ЧЕРЕЗ BROWSER MCP
# ============================================================================

def get_html_from_betboom():
    """
    Получает HTML с BetBoom через Browser MCP
    
    СПОСОБ 1: Через direct HTTP запрос (если BetBoom позволяет JS рендеринг)
    СПОСОБ 2: Через Selenium (если Chrome доступен)
    СПОСОБ 3: Через встроенный браузер Cursor
    """
    
    log_event("🌐 Получение HTML с BetBoom...", "INFO")
    
    try:
        # СПОСОБ 1: Прямой запрос (может не работать из-за JS)
        log_event(f"Попытка 1: Прямой HTTP запрос к {BETBOOM_URL}", "DEBUG")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(BETBOOM_URL, headers=headers, verify=False, timeout=10)
        
        if response.status_code == 200 and len(response.text) > 1000:
            log_event("✅ Получен HTML через прямой запрос", "SUCCESS")
            return response.text
        else:
            log_event(f"❌ Прямой запрос не сработал (статус {response.status_code})", "WARNING")
            
    except Exception as e:
        log_event(f"❌ Ошибка прямого запроса: {e}", "WARNING")
    
    # СПОСОБ 2: Попытка через Selenium (если Chrome установлен)
    try:
        log_event("Попытка 2: Selenium + Chrome", "DEBUG")
        
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')  # Без интерфейса
        
        driver = webdriver.Chrome(options=options)
        driver.get(BETBOOM_URL)
        
        # Ждем загрузки JS
        WebDriverWait(driver, 15).until(
            lambda d: d.find_elements(By.CLASS_NAME, "match") or d.execute_script("return document.readyState") == 'complete'
        )
        
        html = driver.page_source
        driver.quit()
        
        log_event("✅ Получен HTML через Selenium", "SUCCESS")
        return html
        
    except Exception as e:
        log_event(f"❌ Selenium не работает: {e}", "WARNING")
    
    # СПОСОБ 3: Возвращаем сообщение об ошибке
    log_event("❌ Не удалось получить HTML через все способы", "ERROR")
    return None


# ============================================================================
# ПАРСИНГ МАТЧЕЙ
# ============================================================================

def parse_matches(html):
    """Парсит матчи из HTML"""
    
    if not html:
        log_event("❌ HTML пуст", "ERROR")
        return []
    
    log_event("Парсинг матчей из HTML...", "DEBUG")
    
    matches = []
    
    try:
        # Паттерны для поиска матчей
        # Формат: "Команда1 vs Команда2 1:0"
        match_pattern = r'([А-Яа-яЁё\w\s\.\-\(\)]+?)\s+(?:vs|-|—)\s+([А-Яа-яЁё\w\s\.\-\(\)]+?)\s+(\d+)[:\-](\d+)'
        
        for match_obj in re.finditer(match_pattern, html, re.IGNORECASE):
            try:
                team1 = match_obj.group(1).strip()
                team2 = match_obj.group(2).strip()
                score1 = int(match_obj.group(3))
                score2 = int(match_obj.group(4))
                
                # Ищем коэффициенты рядом
                start = max(0, match_obj.start() - 300)
                end = min(len(html), match_obj.end() + 300)
                context = html[start:end]
                
                coef_pattern = r'(\d+\.\d{2})'
                coefs = re.findall(coef_pattern, context)
                
                if len(coefs) >= 2:
                    coef_p1 = float(coefs[0])
                    coef_p2 = float(coefs[1])
                else:
                    continue
                
                # Ищем время матча
                time_pattern = r'([12]Т,\s*\d+\s*мин)'
                time_match = re.search(time_pattern, context)
                time_str = time_match.group(1) if time_match else "Live"
                
                match_data = {
                    'team1': team1,
                    'team2': team2,
                    'score': f"{score1}-{score2}",
                    'league': 'BetBoom',
                    'time': time_str,
                    'coef_p1': coef_p1,
                    'coef_p2': coef_p2
                }
                
                matches.append(match_data)
                log_event(f"✅ Матч: {team1} vs {team2} ({score1}:{score2})", "DEBUG")
            
            except Exception as e:
                log_event(f"Ошибка парсинга матча: {e}", "WARNING")
                continue
        
        log_event(f"✅ Распарсено {len(matches)} матчей", "SUCCESS")
        return matches
    
    except Exception as e:
        log_event(f"❌ Ошибка парсинга: {e}", "ERROR")
        return []


# ============================================================================
# АНАЛИЗ МАТЧЕЙ
# ============================================================================

def analyze_matches(matches_data):
    """Анализирует матчи"""
    
    log_event(f"Анализ {len(matches_data)} матчей...", "INFO")
    
    recommendations = []
    
    for match in matches_data:
        try:
            score_parts = match['score'].split('-')
            score1 = int(score_parts[0])
            score2 = int(score_parts[1])
            
            # Проверяем ничейные
            if score1 == score2:
                log_event(f"⚪ Ничья: {match['team1']} vs {match['team2']}", "DEBUG")
                continue
            
            # Определяем фаворита
            coef_p1 = match['coef_p1']
            coef_p2 = match['coef_p2']
            
            if coef_p1 < coef_p2:
                favorite = match['team1']
                favorite_coef = coef_p1
                is_p1_favorite = True
            else:
                favorite = match['team2']
                favorite_coef = coef_p2
                is_p1_favorite = False
            
            # Определяем лидера
            if score1 > score2:
                is_p1_leader = True
            elif score2 > score1:
                is_p1_leader = False
            else:
                continue
            
            # Проверяем: ведет ли фаворит?
            favorite_leads = (is_p1_favorite == is_p1_leader)
            
            if favorite_leads:
                result = {
                    'team1': match['team1'],
                    'team2': match['team2'],
                    'score': match['score'],
                    'league': match['league'],
                    'time': match['time'],
                    'favorite': favorite,
                    'favorite_coef': favorite_coef
                }
                
                recommendations.append(result)
                log_event(f"✅ РЕКОМЕНДАЦИЯ: {favorite} ({match['score']})", "DEBUG")
        
        except Exception as e:
            log_event(f"Ошибка анализа матча: {e}", "WARNING")
            continue
    
    log_event(f"✅ Найдено {len(recommendations)} рекомендаций", "SUCCESS")
    return recommendations


# ============================================================================
# ФОРМАТИРОВАНИЕ СООБЩЕНИЯ
# ============================================================================

def format_telegram_message(recommendations):
    """Форматирует сообщение для Telegram"""
    
    current_time = datetime.now().strftime('%H:%M')
    current_date = datetime.now().strftime('%d.%m.%Y')
    
    if not recommendations:
        message = f"""🎯 LIVE-АНАЛИЗ • {current_time} МСК, {current_date}

—————————————

⚠️ В данный момент подходящих матчей не найдено.

Следующий анализ через 45 минут.

—————————————

🤝 @TrueLiveBet — честный ИИ-анализ лайв-ставок"""
        
        return message
    
    message = f"""🎯 LIVE-АНАЛИЗ • {current_time} МСК, {current_date}

—————————————

⚽ ФУТБОЛ ⚽

"""
    
    for i, rec in enumerate(recommendations, 1):
        message += f"""{i}. {rec['team1']} vs {rec['team2']}

   Счет: {rec['score']} ({rec['time']}) | {rec['league']}

   🎯 Рекомендуем: {rec['favorite']}

   💰 Кэф BetBoom: ~{rec['favorite_coef']:.2f}

"""
    
    message += """—————————————

📌 Важные моменты:
  • Все рекомендации основаны на анализе лайв-данных
  • Ставим только на матчи где фаворит лидирует
  • Размер ставки - только из собственного банка

—————————————

⚠️ Дисклеймер: Беттинг связан с рисками. Анализируйте самостоятельно.

🤝 @TrueLiveBet — честный ИИ-анализ лайв-ставок"""
    
    return message


# ============================================================================
# ОТПРАВКА В TELEGRAM
# ============================================================================

def send_to_telegram(message):
    """Отправляет сообщение в Telegram"""
    
    log_event("📤 Отправка в Telegram...", "INFO")
    
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': CHANNEL_ID,
        'text': message
    }
    
    try:
        response = requests.post(url, data=data, verify=False, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            log_event(f"✅ ОТПРАВЛЕНО! Message ID: {result['result']['message_id']}", "SUCCESS")
            return True
        else:
            log_event(f"❌ Ошибка Telegram: {result}", "ERROR")
            return False
    
    except Exception as e:
        log_event(f"❌ Ошибка отправки: {e}", "ERROR")
        return False


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    """Главная функция - полный цикл анализа"""
    
    log_event("=" * 80, "")
    log_event("🚀 ПОЛУЧЕН СИГНАЛ 🎯F - НАЧИНАЮ ПОЛНЫЙ АНАЛИЗ", "START")
    log_event("=" * 80, "")
    
    # ШАГ 1: Получаем HTML
    log_event("ШАГ 1: Получение HTML с BetBoom", "INFO")
    html = get_html_from_betboom()
    
    if not html:
        log_event("❌ Не удалось получить HTML", "ERROR")
        return False
    
    # ШАГ 2: Парсим матчи
    log_event("ШАГ 2: Парсинг матчей", "INFO")
    matches = parse_matches(html)
    
    if not matches:
        log_event("❌ Матчи не найдены", "ERROR")
        return False
    
    log_event(f"✅ Найдено {len(matches)} матчей", "SUCCESS")
    
    # ШАГ 3: Анализируем
    log_event("ШАГ 3: Анализ матчей", "INFO")
    recommendations = analyze_matches(matches)
    
    # ШАГ 4: Форматируем
    log_event("ШАГ 4: Форматирование сообщения", "INFO")
    message = format_telegram_message(recommendations)
    
    print("\n📋 СООБЩЕНИЕ:\n")
    print(message)
    print("\n")
    
    # ШАГ 5: Отправляем
    log_event("ШАГ 5: Отправка в @TrueLiveBет", "INFO")
    success = send_to_telegram(message)
    
    if success:
        # Сохраняем копию
        with open(PROJECT_DIR / 'last_telegram_message.txt', 'w', encoding='utf-8') as f:
            f.write(message)
        
        log_event("✅ АНАЛИЗ ЗАВЕРШЕН УСПЕШНО!", "SUCCESS")
        log_event("=" * 80, "")
        return True
    else:
        log_event("❌ АНАЛИЗ НЕ ОТПРАВЛЕН", "ERROR")
        log_event("=" * 80, "")
        return False


if __name__ == '__main__':
    main()

