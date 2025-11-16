#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import glob
from datetime import datetime

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

# ============================================================================
# ПАРСИНГ SNAPSHOT
# ============================================================================

def extract_matches_from_snapshot(snapshot_text):
    """
    Парсит snapshot из Browser MCP и извлекает реальные матчи
    """
    matches = []
    
    # Ищем паттерны вида:
    # - text: Команда1
    # - text: Команда2 0 0 0 0
    # - time: 1Т, 40 мин
    # - button "П1 X.XX"
    # - button "X Y.YY"
    # - button "П2 Z.ZZ"
    
    lines = snapshot_text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Ищем первую команду
        if re.match(r'- text: [А-Я]', line):
            team1_match = re.search(r'- text: (.+)$', line)
            if team1_match:
                team1 = team1_match.group(1).strip()
                
                # Следующая строка - вторая команда со счетом
                i += 1
                if i < len(lines):
                    next_line = lines[i].strip()
                    team2_match = re.search(r'- text: (.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$', next_line)
                    
                    if team2_match:
                        team2 = team2_match.group(1).strip()
                        score_p1 = int(team2_match.group(2))
                        score_p2 = int(team2_match.group(3))
                        score = f"{score_p1}-{score_p2}"
                        
                        # Ищем время
                        time_str = ""
                        league = ""
                        coef_p1 = None
                        coef_p2 = None
                        coef_x = None
                        
                        i += 1
                        while i < len(lines) and (coef_p1 is None or coef_p2 is None or coef_x is None):
                            check_line = lines[i].strip()
                            
                            # Ищем время
                            time_match = re.search(r'- time \[ref=.*?\]: (.+)$', check_line)
                            if time_match and not time_str:
                                time_str = time_match.group(1).strip()
                            
                            # Ищем коэффициенты П1
                            if 'П1' in check_line and coef_p1 is None:
                                coef_match = re.search(r'button "П1 ([\d.]+)"', check_line)
                                if coef_match:
                                    try:
                                        coef_p1 = float(coef_match.group(1))
                                    except:
                                        pass
                            
                            # Ищем коэффициенты X
                            if check_line.startswith('- button "X') and coef_x is None:
                                coef_match = re.search(r'button "X ([\d.]+)"', check_line)
                                if coef_match:
                                    try:
                                        coef_x = float(coef_match.group(1))
                                    except:
                                        pass
                            
                            # Ищем коэффициенты П2
                            if 'П2' in check_line and coef_p2 is None:
                                coef_match = re.search(r'button "П2 ([\d.]+)"', check_line)
                                if coef_match:
                                    try:
                                        coef_p2 = float(coef_match.group(1))
                                    except:
                                        pass
                            
                            # Если собрали все данные - выходим
                            if coef_p1 and coef_p2 and coef_x and time_str:
                                break
                            
                            i += 1
                        
                        # Если собрали данные матча
                        if coef_p1 and coef_p2:
                            matches.append({
                                'team1': team1,
                                'team2': team2,
                                'score': score,
                                'score_p1': score_p1,
                                'score_p2': score_p2,
                                'time': time_str,
                                'coef_p1': coef_p1,
                                'coef_p2': coef_p2,
                                'coef_x': coef_x or 0
                            })
                        
                        i -= 1  # Компенсируем инкремент в цикле
        
        i += 1
    
    return matches

def analyze_matches(matches):
    """
    Анализирует матчи: фаворит ведет или нет?
    """
    recommendations = []
    
    for match in matches:
        # Исключаем ничьи
        if match['score_p1'] == match['score_p2']:
            continue
        
        # Определяем фаворита по коэффициентам
        if match['coef_p1'] < match['coef_p2']:
            favorite_team = match['team1']
            favorite_is_p1 = True
            favorite_coef = match['coef_p1']
        else:
            favorite_team = match['team2']
            favorite_is_p1 = False
            favorite_coef = match['coef_p2']
        
        # Определяем кто ведет
        if match['score_p1'] > match['score_p2']:
            leader_is_p1 = True
        else:
            leader_is_p1 = False
        
        # Проверяем: ведет ли фаворит?
        if favorite_is_p1 == leader_is_p1:
            recommendations.append({
                **match,
                'favorite': favorite_team,
                'favorite_coef': favorite_coef,
                'status': 'ОК'
            })
    
    return recommendations

def format_telegram_message(recommendations):
    """
    Форматирует сообщение для Telegram
    """
    current_time = datetime.now().strftime('%H:%M')
    current_date = datetime.now().strftime('%d.%m.%Y')
    
    message = f"🎯 LIVE-АНАЛИЗ • {current_time} МСК, {current_date}\n\n"
    message += "—————————————\n\n"
    
    if not recommendations:
        message += "❌ В данный момент подходящих матчей для рекомендации не найдено.\n\n"
    else:
        message += "⚽ ФУТБОЛ ⚽\n\n"
        for i, rec in enumerate(recommendations[:3], 1):  # Ограничиваем до 3
            emoji = "🔥" if rec['favorite_coef'] < 1.2 else "💪"
            message += (
                f"{i}. {rec['team1']} vs {rec['team2']}\n\n"
                f"   Счет: {rec['score']} ({rec['time']}) \n\n"
                f"   🎯 Рекомендуем: {rec['favorite']}\n\n"
                f"   📊 Обоснование:\n"
                f"  • {rec['favorite']} - фаворит ({emoji} кэф {rec['favorite_coef']:.2f})\n"
                f"  • На поле контролирует (счет {rec['score']})\n\n"
                f"   💰 Кэф BetBoom: ~{rec['favorite_coef']:.2f}\n\n"
            )
    
    message += "—————————————\n\n"
    message += "📌 Важные моменты:\n"
    message += "  • Все рекомендации основаны на live-анализе BetBoom\n"
    message += "  • Ставим только на матчи где фаворит лидирует\n"
    message += "  • Размер ставки - из собственного банка\n\n"
    message += "—————————————\n\n"
    message += "⚠️ Дисклеймер: Беттинг связан с рисками. Анализируйте самостоятельно.\n\n"
    message += "🤝 @TrueLiveBet — честный ИИ-анализ лайв-ставок\n"
    
    return message

def send_to_telegram(message):
    """
    Отправляет сообщение в Telegram
    """
    BOT_TOKEN = '7824400107:AAGZqPdS0E0N3HsYpD8TW9m8c-bapFd-RHk'
    CHANNEL_ID = '@TrueLiveBet'
    
    print(f"📤 Отправляю в {CHANNEL_ID}...")
    
    try:
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        data = {
            'chat_id': CHANNEL_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=data, verify=False, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            print(f"✅ ОТПРАВЛЕНО в Telegram! Message ID: {result['result']['message_id']}\n")
            return True
        else:
            print(f"❌ Ошибка Telegram: {result}\n")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}\n")
        return False

# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    print("\n" + "="*80)
    print("🚀 ПОЛУЧЕНИЕ + АНАЛИЗ РЕАЛЬНЫХ МАТЧЕЙ ИЗ SNAPSHOT")
    print("="*80 + "\n")
    
    # Ищем последний snapshot от Browser MCP
    snapshots = sorted(
        glob.glob(r'c:\Users\Мария\.cursor\projects\d-cursor-Backtothestart-09-11-2025\agent-tools\*.txt'),
        key=os.path.getmtime,
        reverse=True
    )
    
    if not snapshots:
        print("❌ Snapshot не найден!\n")
        return
    
    snapshot_file = snapshots[0]
    print(f"📥 Загружаю snapshot: {os.path.basename(snapshot_file)}\n")
    
    with open(snapshot_file, 'r', encoding='utf-8') as f:
        snapshot_text = f.read()
    
    # Парсим матчи
    print("🔍 Парсирую матчи...\n")
    matches = extract_matches_from_snapshot(snapshot_text)
    print(f"✅ Найдено матчей: {len(matches)}\n")
    
    if not matches:
        print("❌ Матчи не распарсены из snapshot\n")
        return
    
    # Показываем найденные матчи
    print("📊 НАЙДЕННЫЕ МАТЧИ:")
    for i, m in enumerate(matches[:10], 1):
        print(f"  {i}. {m['team1']} vs {m['team2']} ({m['score']}) - {m['time']}")
        print(f"     Кэфы: П1={m['coef_p1']:.2f} X={m['coef_x']:.2f} П2={m['coef_p2']:.2f}\n")
    
    # Анализируем
    print("\n🔍 АНАЛИЗИРУЮ: фаворит ведет или нет?...\n")
    recommendations = analyze_matches(matches)
    print(f"✅ Подходящих матчей: {len(recommendations)}\n")
    
    if recommendations:
        print("📋 РЕКОМЕНДАЦИИ:")
        for i, rec in enumerate(recommendations[:10], 1):
            print(f"  {i}. {rec['team1']} vs {rec['team2']} ({rec['score']})")
            print(f"     → Ставить на {rec['favorite']} (кэф {rec['favorite_coef']:.2f})\n")
    
    # Форматируем и отправляем в Telegram
    print("\n📋 ФОРМАТИРУЮ СООБЩЕНИЕ...\n")
    message = format_telegram_message(recommendations)
    
    print("=" * 80)
    print("СООБЩЕНИЕ ДЛЯ TELEGRAM:")
    print("=" * 80)
    print(message)
    print("=" * 80 + "\n")
    
    send_to_telegram(message)

if __name__ == '__main__':
    main()

