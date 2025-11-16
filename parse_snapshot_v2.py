#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import glob
from datetime import datetime

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

def extract_matches_from_snapshot(snapshot_text):
    """
    Парсит snapshot из Browser MCP и извлекает матчи
    Ищет паттерны:
    - text: Команда1
    - text: Команда2 SCORE1 X SCORE2 X
    - time: 1Т, 40 мин
    - button "П1 X.XX"
    - button "X Y.YY"  
    - button "П2 Z.ZZ"
    """
    matches = []
    lines = snapshot_text.split('\n')
    
    print(f"📊 Всего строк в snapshot: {len(lines)}")
    print("🔍 Ищу паттерны матчей...\n")
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Ищем текст первой команды (текст с кириллицей после "- text:")
        if '- text:' in line and any(c in 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ' for c in line):
            # Извлекаем первую команду
            team1_match = re.search(r'- text:\s*(.+)$', line)
            if not team1_match:
                i += 1
                continue
            
            team1 = team1_match.group(1).strip()
            
            # Проверяем, это ли названия лиг или фильтров (пропускаем)
            if any(x in team1 for x in ['Премьер', 'Лига', 'Серия', 'Бундеслига', 'Примера', 'Лилль', 'Исход', 'Тотал', 'Фора']):
                i += 1
                continue
            
            print(f"  🔎 Найдена команда 1: {team1}")
            
            # Ищем вторую команду со счетом (она должна быть близко)
            team2 = None
            score_p1 = None
            score_p2 = None
            j = i + 1
            
            while j < min(i + 20, len(lines)):  # Ищем в соседних 20 строках
                next_line = lines[j]
                
                # Паттерн второй команды: "- text: КомандаНазвание N N N N"
                team2_pattern = r'- text:\s*(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$'
                team2_match = re.search(team2_pattern, next_line)
                
                if team2_match:
                    team2_candidate = team2_match.group(1).strip()
                    
                    # Проверяем что это не фильтр/лига
                    if not any(x in team2_candidate for x in ['Премьер', 'Лига', 'Серия', 'Бундеслига', 'live', 'icon', '+']):
                        team2 = team2_candidate
                        score_p1 = int(team2_match.group(2))
                        score_p2 = int(team2_match.group(3))
                        print(f"     + Найдена команда 2: {team2} (счет {score_p1}-{score_p2})")
                        
                        # Теперь ищем время и коэффициенты
                        time_str = ""
                        coef_p1 = None
                        coef_x = None
                        coef_p2 = None
                        
                        k = j + 1
                        while k < min(j + 30, len(lines)):
                            check_line = lines[k]
                            
                            # Ищем время
                            if '- time' in check_line and not time_str:
                                time_match = re.search(r'- time.*?:\s*(.+?)$', check_line)
                                if time_match:
                                    time_str = time_match.group(1).strip()
                                    print(f"     + Найдено время: {time_str}")
                            
                            # Ищем коэффициенты
                            if 'button' in check_line and 'П1' in check_line and coef_p1 is None:
                                coef_match = re.search(r'button "П1\s+([\d.]+)"', check_line)
                                if coef_match:
                                    coef_p1 = float(coef_match.group(1))
                                    print(f"     + Кэф П1: {coef_p1}")
                            
                            if 'button' in check_line and check_line.strip().startswith('- button "X') and coef_x is None:
                                coef_match = re.search(r'button "X\s+([\d.]+)"', check_line)
                                if coef_match:
                                    coef_x = float(coef_match.group(1))
                                    print(f"     + Кэф X: {coef_x}")
                            
                            if 'button' in check_line and 'П2' in check_line and coef_p2 is None:
                                coef_match = re.search(r'button "П2\s+([\d.]+)"', check_line)
                                if coef_match:
                                    coef_p2 = float(coef_match.group(1))
                                    print(f"     + Кэф П2: {coef_p2}")
                            
                            # Если нашли все - выходим
                            if coef_p1 and coef_p2 and time_str:
                                break
                            
                            k += 1
                        
                        # Добавляем матч если нашли основные данные
                        if coef_p1 and coef_p2:
                            matches.append({
                                'team1': team1,
                                'team2': team2,
                                'score': f"{score_p1}-{score_p2}",
                                'score_p1': score_p1,
                                'score_p2': score_p2,
                                'time': time_str,
                                'coef_p1': coef_p1,
                                'coef_p2': coef_p2,
                                'coef_x': coef_x or 1.0
                            })
                            print(f"     ✅ МАТЧ ДОБАВЛЕН!\n")
                        
                        break
                
                j += 1
        
        i += 1
    
    return matches

def analyze_matches(matches):
    """Анализирует матчи"""
    recommendations = []
    
    for match in matches:
        # Исключаем ничьи
        if match['score_p1'] == match['score_p2']:
            continue
        
        # Определяем фаворита
        if match['coef_p1'] < match['coef_p2']:
            favorite_team = match['team1']
            favorite_is_p1 = True
            favorite_coef = match['coef_p1']
        else:
            favorite_team = match['team2']
            favorite_is_p1 = False
            favorite_coef = match['coef_p2']
        
        # Кто ведет?
        leader_is_p1 = match['score_p1'] > match['score_p2']
        
        # Фаворит ведет?
        if favorite_is_p1 == leader_is_p1:
            recommendations.append({
                **match,
                'favorite': favorite_team,
                'favorite_coef': favorite_coef
            })
    
    return recommendations

def format_telegram_message(recommendations):
    current_time = datetime.now().strftime('%H:%M')
    current_date = datetime.now().strftime('%d.%m.%Y')
    
    message = f"🎯 LIVE-АНАЛИЗ • {current_time} МСК, {current_date}\n\n"
    message += "—————————————\n\n"
    
    if not recommendations:
        message += "❌ В данный момент подходящих матчей не найдено.\n\n"
    else:
        message += "⚽ ФУТБОЛ ⚽\n\n"
        for i, rec in enumerate(recommendations[:3], 1):
            emoji = "🔥" if rec['favorite_coef'] < 1.2 else "💪"
            message += (
                f"{i}. {rec['team1']} vs {rec['team2']}\n\n"
                f"   Счет: {rec['score']} ({rec['time']})\n\n"
                f"   🎯 Рекомендуем: {rec['favorite']}\n\n"
                f"   📊 Обоснование:\n"
                f"  • {rec['favorite']} - фаворит ({emoji} кэф {rec['favorite_coef']:.2f})\n"
                f"  • На поле контролирует (счет {rec['score']})\n\n"
                f"   💰 Кэф BetBoom: ~{rec['favorite_coef']:.2f}\n\n"
            )
    
    message += "—————————————\n\n"
    message += "📌 Важное:\n"
    message += "  • Ставим на фаворита когда он лидирует\n"
    message += "  • Беттинг - на деньги\n\n"
    message += "⚠️ Дисклеймер: Анализируйте самостоятельно перед ставкой.\n\n"
    message += "🤝 @TrueLiveBet — ИИ-анализ лайв-ставок\n"
    
    return message

def send_to_telegram(message):
    BOT_TOKEN = '7824400107:AAGZqPdS0E0N3HsYpD8TW9m8c-bapFd-RHk'
    CHANNEL_ID = '@TrueLiveBet'
    
    try:
        import requests
        import urllib3
        urllib3.disable_warnings()
        
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        response = requests.post(url, data={'chat_id': CHANNEL_ID, 'text': message}, verify=False, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            print(f"✅ ОТПРАВЛЕНО! Message ID: {result['result']['message_id']}\n")
            return True
        else:
            print(f"❌ Ошибка: {result}\n")
            return False
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}\n")
        return False

def main():
    print("\n" + "="*80)
    print("🚀 ПАРСИНГ SNAPSHOT + АНАЛИЗ + ОТПРАВКА")
    print("="*80 + "\n")
    
    # Загружаем последний snapshot
    snapshots = sorted(
        glob.glob(r'c:\Users\Мария\.cursor\projects\d-cursor-Backtothestart-09-11-2025\agent-tools\*.txt'),
        key=os.path.getmtime,
        reverse=True
    )
    
    if not snapshots:
        print("❌ Snapshot не найден!\n")
        return
    
    print(f"📥 Загружаю: {os.path.basename(snapshots[0])}\n")
    
    with open(snapshots[0], 'r', encoding='utf-8') as f:
        snapshot_text = f.read()
    
    # Парсим
    matches = extract_matches_from_snapshot(snapshot_text)
    print(f"\n✅ ИТОГО НАЙДЕНО: {len(matches)} матчей\n")
    
    if matches:
        print("📊 НАЙДЕННЫЕ МАТЧИ:")
        for m in matches[:5]:
            print(f"  • {m['team1']} vs {m['team2']} ({m['score']}) - {m['time']}")
            print(f"    П1={m['coef_p1']:.2f} X={m['coef_x']:.2f} П2={m['coef_p2']:.2f}\n")
    
    # Анализируем
    recommendations = analyze_matches(matches)
    print(f"📈 Подходящих матчей: {len(recommendations)}\n")
    
    # Отправляем
    message = format_telegram_message(recommendations)
    print("=" * 80)
    print(message)
    print("=" * 80 + "\n")
    
    send_to_telegram(message)

if __name__ == '__main__':
    main()

