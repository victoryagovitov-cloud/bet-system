#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ФИНАЛЬНАЯ АВТОНОМНАЯ СИСТЕМА - Полностью готова!

Когда получу сигнал 🎯F:
1. Открываю BetBoom через Browser MCP
2. Получаю snapshot (HTML)
3. Парсю матчи
4. Анализирую
5. Отправляю в @TrueLiveBет

ВСЁ АВТОМАТИЧЕСКИ!
"""

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.stdout.reconfigure(encoding='utf-8')

import requests
import re
import json
from datetime import datetime
from pathlib import Path
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

PROJECT_DIR = Path(__file__).parent
LOG_FILE = PROJECT_DIR / "final_system.log"
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
# ПАРСИНГ МАТЧЕЙ ИЗ HTML
# ============================================================================

def parse_matches_from_html(html_content):
    """Парсит матчи из HTML BetBoom"""
    
    if not html_content:
        log_event("❌ HTML пуст", "ERROR")
        return []
    
    log_event(f"Парсинг HTML ({len(html_content)} символов)...", "DEBUG")
    
    matches = []
    
    try:
        # Ищем в HTML данные о матчах
        # BetBoom использует специфичный HTML-формат
        
        # Паттерн 1: Ищем блоки с командами и счетом
        match_pattern = r'([А-Яа-яЁё\w\s\.\-\(\)]+?)\s+(\d+)[:\-](\d+)\s+([А-Яа-яЁё\w\s\.\-\(\)]+?)'
        
        for match_obj in re.finditer(match_pattern, html_content):
            try:
                team1 = match_obj.group(1).strip()
                score1 = int(match_obj.group(2))
                score2 = int(match_obj.group(3))
                team2 = match_obj.group(4).strip()
                
                # Пропускаем если очень короткие названия (скорее всего шум)
                if len(team1) < 3 or len(team2) < 3:
                    continue
                
                # Ищем коэффициенты рядом
                start = max(0, match_obj.start() - 500)
                end = min(len(html_content), match_obj.end() + 500)
                context = html_content[start:end]
                
                coef_pattern = r'(\d+\.\d{2})'
                coefs = re.findall(coef_pattern, context)
                
                if len(coefs) >= 2:
                    coef_p1 = float(coefs[0])
                    coef_p2 = float(coefs[1])
                else:
                    coef_p1 = 2.0
                    coef_p2 = 2.0
                
                # Ищем время матча
                time_pattern = r'([12]Т,\s*\d+\s*мин)'
                time_match = re.search(time_pattern, context)
                time_str = time_match.group(1) if time_match else "Live"
                
                # Ищем лигу
                league_pattern = r'([\w\s\.\-]+?[Л|л]ига)'
                league_match = re.search(league_pattern, context)
                league = league_match.group(1) if league_match else "BetBoom Live"
                
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
                log_event(f"✅ Матч: {team1} {score1}:{score2} {team2}", "DEBUG")
            
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
    
    log_event(f"📊 Анализ {len(matches_data)} матчей...", "INFO")
    
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
            
            # Определяем фаворита по коэффициентам
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
                log_event(f"✅ РЕКОМЕНДУЕМ: {favorite} ({match['score']})", "DEBUG")
        
        except Exception as e:
            log_event(f"Ошибка анализа: {e}", "WARNING")
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

🤝 @TrueLiveBet — честный ИИ-анализ"""
        
        return message
    
    message = f"""🎯 LIVE-АНАЛИЗ • {current_time} МСК, {current_date}

—————————————

⚽ ФУТБОЛ ⚽

"""
    
    for i, rec in enumerate(recommendations, 1):
        message += f"""{i}. {rec['team1']} vs {rec['team2']}

   Счет: {rec['score']} ({rec['time']}) | {rec['league']}

   🎯 Рекомендуем: {rec['favorite']}

   💰 Кэф: ~{rec['favorite_coef']:.2f}

"""
    
    message += """—————————————

📌 Основано на анализе текущих данных BetBoom

⚠️ Дисклеймер: Беттинг связан с рисками.

🤝 @TrueLiveBet"""
    
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
        response = requests.post(url, data=data, verify=False, timeout=15)
        result = response.json()
        
        if result.get('ok'):
            log_event(f"✅ ОТПРАВЛЕНО! ID: {result['result']['message_id']}", "SUCCESS")
            return True
        else:
            log_event(f"❌ Ошибка: {result}", "ERROR")
            return False
    
    except Exception as e:
        log_event(f"❌ Ошибка: {e}", "ERROR")
        return False


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def main(html_content):
    """
    Главная функция - полный цикл анализа
    
    Параметры:
    - html_content: HTML с BetBoom полученный через Browser MCP
    """
    
    log_event("=" * 80, "")
    log_event("🚀 НАЧИНАЮ АНАЛИЗ LIVE-МАТЧЕЙ", "START")
    log_event("=" * 80, "")
    
    # ШАГ 1: Парсим матчи
    log_event("ШАГ 1: Парсинг HTML", "INFO")
    matches = parse_matches_from_html(html_content)
    
    if not matches:
        log_event("❌ Матчи не найдены", "ERROR")
        return False
    
    # ШАГ 2: Анализируем
    log_event("ШАГ 2: Анализ матчей", "INFO")
    recommendations = analyze_matches(matches)
    
    # ШАГ 3: Форматируем
    log_event("ШАГ 3: Форматирование", "INFO")
    message = format_telegram_message(recommendations)
    
    print("\n📋 СООБЩЕНИЕ:\n")
    print(message)
    print("\n")
    
    # ШАГ 4: Отправляем
    log_event("ШАГ 4: Отправка в @TrueLiveBет", "INFO")
    success = send_to_telegram(message)
    
    if success:
        with open(PROJECT_DIR / 'last_message.txt', 'w', encoding='utf-8') as f:
            f.write(message)
        
        log_event("✅ АНАЛИЗ ЗАВЕРШЕН!", "SUCCESS")
        log_event("=" * 80, "")
        return True
    else:
        log_event("❌ ОШИБКА ОТПРАВКИ", "ERROR")
        log_event("=" * 80, "")
        return False


if __name__ == '__main__':
    print("\n⚠️ ИНСТРУКЦИЯ:\n")
    print("Этот скрипт получает HTML от Browser MCP и анализирует его")
    print("Используй его через другой скрипт который передает HTML\n")

