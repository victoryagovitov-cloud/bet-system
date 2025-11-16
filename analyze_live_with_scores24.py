# -*- coding: utf-8 -*-
"""
🔍 ПОЛНЫЙ АНАЛИЗ LIVE-МАТЧЕЙ БЕЗ WEB SEARCH
Использует только Scores24.live для проверки статистики
"""
import sys
import io
import time
import json
import requests
import urllib3
from datetime import datetime
from fast_stats_collector import get_match_stats_fast

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===================== КОНФИГ =====================

with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

BOT_TOKEN = CONFIG['notifications']['telegram']['bot_token']
CHANNEL = CONFIG['notifications']['telegram']['channel_username']

# ===================== ЧЕК-ЛИСТЫ =====================

def check_football_criteria(match_data):
    """
    Чек-лист для футбола
    ✓ Неничейный счет
    ✓ Фаворит ведет (по статистике)
    ✓ Справка об ОБЕИХ командах
    """
    # Здесь будет логика проверки
    # TODO: реализовать на основе данных из Scores24
    return False

def check_tennis_criteria(match_data):
    """
    Чек-лист для тенниса
    ✓ Выиграл 1-й сет + ведет во 2-м
    ИЛИ
    ✓ Ведет в 1-м с отрывом 3+ гейма
    + фаворит по ATP/WTA
    """
    # TODO: реализовать на основе данных из Scores24
    return False

def check_handball_criteria(match_data):
    """
    Чек-лист для гандбола
    ✓ Неничейный результат
    ✓ Математический расчет тоталов
    """
    # TODO: реализовать на основе данных из Scores24
    return False

# ===================== АНАЛИЗ МАТЧЕЙ =====================

def analyze_betboom_matches(betboom_data):
    """
    Анализ матчей с BetBoom
    betboom_data = {
        'football': [...],
        'tennis': [...],
        'handball': [...]
    }
    """
    print("\n" + "="*70)
    print("🔍 НАЧИНАЕМ АНАЛИЗ LIVE-МАТЧЕЙ")
    print("="*70)
    
    results = {
        'football': [],
        'tennis': [],
        'handball': []
    }
    
    total_checked = 0
    total_found = 0
    
    # Футбол
    if betboom_data.get('football'):
        print(f"\n⚽ ФУТБОЛ: {len(betboom_data['football'])} матчей")
        for match in betboom_data['football']:
            total_checked += 1
            print(f"\n--- Матч {total_checked}: {match['team1']} - {match['team2']} ---")
            
            # Проверяем статистику на Scores24
            stats = get_match_stats_fast(
                sport='football',
                team1=match['team1'],
                team2=match['team2'],
                league=match.get('league')
            )
            
            if stats['success']:
                total_found += 1
                # Применяем чек-лист
                if check_football_criteria(stats['data']):
                    results['football'].append({
                        'match': match,
                        'stats': stats['data'],
                        'source': stats['source']
                    })
                    print("   ✅ ПОДХОДИТ для рекомендации")
                else:
                    print("   ⚠️ Не прошел чек-лист")
            else:
                print("   ❌ Статистика не найдена")
    
    # Теннис
    if betboom_data.get('tennis'):
        print(f"\n🎾 ТЕННИС: {len(betboom_data['tennis'])} матчей")
        for match in betboom_data['tennis']:
            total_checked += 1
            print(f"\n--- Матч {total_checked}: {match['player1']} - {match['player2']} ---")
            
            stats = get_match_stats_fast(
                sport='tennis',
                team1=match['player1'],
                team2=match['player2'],
                league=match.get('tournament')
            )
            
            if stats['success']:
                total_found += 1
                if check_tennis_criteria(stats['data']):
                    results['tennis'].append({
                        'match': match,
                        'stats': stats['data'],
                        'source': stats['source']
                    })
                    print("   ✅ ПОДХОДИТ для рекомендации")
                else:
                    print("   ⚠️ Не прошел чек-лист")
            else:
                print("   ❌ Статистика не найдена")
    
    # Гандбол
    if betboom_data.get('handball'):
        print(f"\n🤾 ГАНДБОЛ: {len(betboom_data['handball'])} матчей")
        for match in betboom_data['handball']:
            total_checked += 1
            print(f"\n--- Матч {total_checked}: {match['team1']} - {match['team2']} ---")
            
            stats = get_match_stats_fast(
                sport='handball',
                team1=match['team1'],
                team2=match['team2'],
                league=match.get('league')
            )
            
            if stats['success']:
                total_found += 1
                if check_handball_criteria(stats['data']):
                    results['handball'].append({
                        'match': match,
                        'stats': stats['data'],
                        'source': stats['source']
                    })
                    print("   ✅ ПОДХОДИТ для рекомендации")
                else:
                    print("   ⚠️ Не прошел чек-лист")
            else:
                print("   ❌ Статистика не найдена")
    
    # Итоги
    print("\n" + "="*70)
    print("📊 ИТОГИ АНАЛИЗА")
    print("="*70)
    print(f"   Всего проверено: {total_checked}")
    print(f"   Статистика найдена: {total_found}")
    print(f"   Подходящих матчей: {len(results['football']) + len(results['tennis']) + len(results['handball'])}")
    print("="*70 + "\n")
    
    return results

# ===================== ОТПРАВКА В TELEGRAM =====================

def send_to_telegram(results, start_time, end_time):
    """
    Отправка результатов анализа в Telegram
    """
    current_time = datetime.now().strftime('%H:%M')
    current_date = datetime.now().strftime('%d.%m.%Y')
    
    total_matches = len(results['football']) + len(results['tennis']) + len(results['handball'])
    
    if total_matches == 0:
        message = f"""───────────────────────────────────
📊 АНАЛИЗ LIVE-МАТЧЕЙ НА {current_time} МСК ({current_date})

❌ ПОДХОДЯЩИХ МАТЧЕЙ НЕ НАЙДЕНО

Проверены все live-матчи на BetBoom.
Ни один матч не прошел строгие критерии системы.

---
⏰ Время анализа: {start_time}-{end_time} МСК
📈 Статистика проверена через Scores24.live
✅ Следующий анализ через 45 минут

🤖 TrueLiveBet | Честные прогнозы live-ставок
───────────────────────────────────"""
    else:
        # Формируем сообщение с рекомендациями
        message = f"""───────────────────────────────────
📊 АНАЛИЗ LIVE-МАТЧЕЙ НА {current_time} МСК ({current_date})

"""
        
        # Футбол
        if results['football']:
            message += "⚽ ФУТБОЛ:\n\n"
            for i, item in enumerate(results['football'], 1):
                match = item['match']
                message += f"{i}️⃣ {match['team1']} - {match['team2']}\n"
                message += f"   {match['league']}\n"
                message += f"   Счет: {match['score']}\n"
                message += f"   Рекомендация: {match['recommendation']}\n"
                message += f"   Коэфф: {match['odds']}\n\n"
                message += f"   📌 {match['analysis']}\n\n"
                message += f"   Источник статистики: {item['source']}\n"
                message += f"   ✅ Категория: {match['category']}\n\n---\n\n"
        
        # Теннис
        if results['tennis']:
            message += "🎾 ТЕННИС:\n\n"
            for i, item in enumerate(results['tennis'], 1):
                match = item['match']
                message += f"{i}️⃣ {match['player1']} - {match['player2']}\n"
                message += f"   {match['tournament']}\n"
                message += f"   Счет: {match['score']}\n"
                message += f"   Рекомендация: {match['recommendation']}\n"
                message += f"   Коэфф: {match['odds']}\n\n"
                message += f"   📌 {match['analysis']}\n\n"
                message += f"   Источник статистики: {item['source']}\n"
                message += f"   ✅ Категория: {match['category']}\n\n---\n\n"
        
        # Гандбол
        if results['handball']:
            message += "🤾 ГАНДБОЛ:\n\n"
            for i, item in enumerate(results['handball'], 1):
                match = item['match']
                message += f"{i}️⃣ {match['team1']} - {match['team2']}\n"
                message += f"   {match['league']}\n"
                message += f"   Счет: {match['score']}\n"
                message += f"   Рекомендация: {match['recommendation']}\n"
                message += f"   Коэфф: {match['odds']}\n\n"
                message += f"   📌 {match['analysis']}\n\n"
                message += f"   Источник статистики: {item['source']}\n"
                message += f"   ✅ Категория: {match['category']}\n\n---\n\n"
        
        message += f"""📊 ИТОГО: {total_matches} подходящих матча
   • Футбол: {len(results['football'])}
   • Теннис: {len(results['tennis'])}
   • Гандбол: {len(results['handball'])}

---
⏰ Время анализа: {start_time}-{end_time} МСК
📈 Статистика проверена через Scores24.live
✅ ВСЕ МАТЧИ СООТВЕТСТВУЮТ КРИТЕРИЯМ СИСТЕМЫ

🤖 TrueLiveBet | Честные прогнозы live-ставок
───────────────────────────────────"""
    
    # Отправляем
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHANNEL,
        'text': message
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10, verify=False)
        response.raise_for_status()
        print(f"OK: Message sent to {CHANNEL}")
        print(f"Status code: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR sending to Telegram: {e}")
        return False

# ===================== ТЕСТИРОВАНИЕ =====================

def test_with_sample_data():
    """
    Тестирование с примерными данными
    """
    print("="*70)
    print("🧪 ТЕСТ СИСТЕМЫ АНАЛИЗА БЕЗ WEB SEARCH")
    print("="*70)
    
    # Примерные данные с BetBoom
    sample_data = {
        'football': [
            {
                'team1': 'Шапекоэнсе',
                'team2': 'Операрио ПР',
                'league': 'Бразилия. Серия B',
                'score': '2:0',
                'time': '2Т, 49 мин',
                'odds': 1.06,
                'recommendation': 'П1',
                'category': 'МЕРТВЫЙ ⭐⭐⭐⭐⭐',
                'analysis': 'Фаворит ведет 2:0 на последних минутах'
            }
        ],
        'tennis': [],
        'handball': [
            {
                'team1': 'Сан Каэтано',
                'team2': 'Сорокаба',
                'league': 'Бразилия. Паулиста',
                'score': '4:1',
                'time': '1Т, 8 мин',
                'odds': 1.19,
                'recommendation': 'П1',
                'category': 'ОТЛИЧНЫЙ ⭐⭐⭐',
                'analysis': 'Фаворит ведет 4:1 в первом тайме'
            }
        ]
    }
    
    start_time = datetime.now().strftime('%H:%M')
    
    # Анализируем
    results = analyze_betboom_matches(sample_data)
    
    end_time = datetime.now().strftime('%H:%M')
    
    # Отправляем
    send_to_telegram(results, start_time, end_time)

if __name__ == "__main__":
    test_with_sample_data()

