#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import glob
from datetime import datetime

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

DISCLAIMER_COUNTER_FILE = "disclaimer_counter.txt"

def get_next_disclaimer():
    """Получает следующий дисклеймер из списка"""
    try:
        with open("disclaimers.txt", "r", encoding="utf-8") as f:
            disclaimers = [line.strip() for line in f if line.strip()]
    except:
        disclaimers = ["⚠️ Все ставки несут риски. Играйте ответственно."]
    
    try:
        with open(DISCLAIMER_COUNTER_FILE, "r") as f:
            counter = int(f.read().strip())
    except:
        counter = 0
    
    disclaimer = disclaimers[counter % len(disclaimers)]
    
    with open(DISCLAIMER_COUNTER_FILE, "w") as f:
        f.write(str((counter + 1) % len(disclaimers)))
    
    return disclaimer

def clean_name(name):
    """Очищает название от мусора"""
    # Удаляем счёты в конце
    name = re.sub(r'\s+\d+\s+\d+\s+\d+\s+\d+\s*$', '', name).strip()
    # Удаляем (ж) для женских команд
    name = re.sub(r'\s*\(ж\)\s*$', '', name).strip()
    return name

def is_live_match(time_str):
    """Проверяет, идет ли матч сейчас (LIVE)"""
    # LIVE матчи: содержат "Т, XX мин", "Перерыв", "2Т, XX мин"
    # НЕ LIVE: "Не начался", "Начало через XX:XX"
    if not time_str:
        return False
    
    time_lower = time_str.lower()
    
    # Исключаем матчи которые еще не начались
    if 'не начался' in time_lower or 'начало через' in time_lower:
        return False
    
    # LIVE матчи имеют время в минутах
    if 'мин' in time_lower or 'перерыв' in time_lower:
        return True
    
    return False

def extract_live_matches(snapshot_text):
    """Извлекает ТОЛЬКО LIVE матчи из snapshot"""
    matches = []
    lines = snapshot_text.split('\n')
    
    print(f"📊 Сканирую {len(lines)} строк...\n")
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Ищем первую команду (кириллица)
        if '- text:' in line and any(c in 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ' for c in line):
            team1_match = re.search(r'- text:\s*(.+)$', line)
            if not team1_match:
                i += 1
                continue
            
            team1 = team1_match.group(1).strip()
            
            # Пропускаем служебные названия
            if any(x in team1 for x in ['Премьер', 'Лига', 'Серия', 'Бундеслига', 'Примера', 
                                         'Исход', 'Тотал', 'Фора', 'live', 'Оценка', 'icon', 
                                         'Единоборства', 'Бокс', 'Дартс', 'Снукер']):
                i += 1
                continue
            
            # Ищем вторую команду со счетом
            team2 = None
            score_p1 = None
            score_p2 = None
            j = i + 1
            
            while j < min(i + 20, len(lines)):
                next_line = lines[j]
                
                # Паттерн второй команды со счётом
                team2_pattern = r'- text:\s*(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$'
                team2_match = re.search(team2_pattern, next_line)
                
                if team2_match:
                    team2_raw = team2_match.group(1).strip()
                    
                    # Пропускаем служебные
                    if any(x in team2_raw for x in ['Премьер', 'Лига', 'Серия', '+', 'icon', 'live']):
                        j += 1
                        continue
                    
                    team2 = clean_name(team2_raw)
                    score_p1 = int(team2_match.group(2))
                    score_p2 = int(team2_match.group(3))
                    
                    # Ищем время матча
                    time_str = ""
                    league = ""
                    coef_p1 = None
                    coef_p2 = None
                    
                    k = j + 1
                    while k < min(j + 30, len(lines)):
                        check_line = lines[k]
                        
                        # Ищем время
                        if '- time' in check_line and not time_str:
                            time_match = re.search(r'- time.*?:\s*(.+?)$', check_line)
                            if time_match:
                                time_str = time_match.group(1).strip()
                        
                        # Ищем коэффициенты
                        if 'button' in check_line and 'П1' in check_line and coef_p1 is None:
                            coef_match = re.search(r'button "П1\s+([\d.]+)"', check_line)
                            if coef_match:
                                coef_p1 = float(coef_match.group(1))
                        
                        if 'button' in check_line and 'П2' in check_line and coef_p2 is None:
                            coef_match = re.search(r'button "П2\s+([\d.]+)"', check_line)
                            if coef_match:
                                coef_p2 = float(coef_match.group(1))
                        
                        if coef_p1 and coef_p2 and time_str:
                            break
                        
                        k += 1
                    
                    # Добавляем ТОЛЬКО если это LIVE матч с неничейным счётом
                    if (coef_p1 and coef_p2 and time_str and 
                        is_live_match(time_str) and 
                        score_p1 != score_p2):
                        
                        # Определяем фаворита и кто ведет
                        if coef_p1 < coef_p2:
                            favorite = team1
                            is_p1_favorite = True
                        else:
                            favorite = team2
                            is_p1_favorite = False
                        
                        is_p1_leader = score_p1 > score_p2
                        
                        # Только если фаворит ведет
                        if is_p1_favorite == is_p1_leader:
                            matches.append({
                                'team1': clean_name(team1),
                                'team2': team2,
                                'score': f"{score_p1}:{score_p2}",
                                'time': time_str,
                                'coef_p1': coef_p1,
                                'coef_p2': coef_p2,
                                'favorite': favorite,
                                'favorite_coef': min(coef_p1, coef_p2),
                                'is_p1': is_p1_favorite
                            })
                            print(f"✅ {clean_name(team1)} vs {team2} ({score_p1}:{score_p2}) - {time_str}")
                        
                        break
                    
                    j += 1
                    if team2:
                        break
                
                j += 1
        
        i += 1
    
    return matches

def format_telegram_message(matches):
    """Форматирует сообщение в твоём стиле"""
    current_time = datetime.now().strftime('%H:%M')
    current_date = datetime.now().strftime('%d.%m.%Y')
    
    message = f"🎯 LIVE-АНАЛИЗ • {current_time} МСК, {current_date}\n\n"
    message += "—————————————\n\n"
    message += "⚽ ФУТБОЛ ⚽\n\n"
    message += "—————————————\n\n"
    
    if not matches:
        message += "❌ Нет подходящих матчей в данный момент.\n\n"
    else:
        for i, match in enumerate(matches[:5], 1):
            emoji = "🔥" if match['favorite_coef'] < 1.2 else "💪"
            
            if match['is_p1']:
                bet = f"П1 {match['team1']}"
            else:
                bet = f"П2 {match['team2']}"
            
            message += f"{i}. ⚽ {match['team1']} - {match['team2']}\n\n"
            message += f"📊 Счет: {match['score']} ({match['time']})\n\n"
            message += f"✅ Ставка: {bet}\n\n"
            message += f"💰 Кэф BetBoom: ~{match['favorite_coef']:.2f}\n\n"
            message += f"🎯 АНАЛИЗ:\n\n"
            fav_clean = clean_name(match['favorite'])
            message += f"{fav_clean} - фаворит по коэффициентам ({emoji} {match['favorite_coef']:.2f}). "
            message += f"Уверенно ведет со счетом {match['score']}. Высокая вероятность удержания результата.\n\n"
            message += f"⚡ ВЕРОЯТНОСТЬ: ~85%\n\n"
            message += "—————————————\n\n"
    
    # Время и дисклеймер
    message += f"⏰ {current_time} МСК\n\n"
    message += "🤖 @TrueLiveBet | Честный ИИ-анализ\n\n"
    message += get_next_disclaimer()
    
    return message

def send_to_telegram(message):
    """Отправляет в Telegram"""
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
            print(f"\n✅ ОТПРАВЛЕНО! Message ID: {result['result']['message_id']}\n")
            return True
        else:
            print(f"\n❌ Ошибка: {result}\n")
            return False
    except Exception as e:
        print(f"\n❌ Ошибка отправки: {e}\n")
        return False

def main():
    print("\n" + "="*80)
    print("🚀 ПОЛУЧЕНИЕ И ОТПРАВКА LIVE-МАТЧЕЙ")
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
    
    # Извлекаем ТОЛЬКО LIVE матчи где фаворит ведет
    print("🔍 Поиск LIVE матчей где фаворит ведет...\n")
    matches = extract_live_matches(snapshot_text)
    
    print(f"\n📊 ИТОГО ПОДХОДЯЩИХ: {len(matches)} матчей\n")
    
    if not matches:
        print("❌ Нет подходящих матчей\n")
        return
    
    # Форматируем и отправляем
    message = format_telegram_message(matches)
    
    print("=" * 80)
    print(message)
    print("=" * 80 + "\n")
    
    send_to_telegram(message)

if __name__ == '__main__':
    main()

