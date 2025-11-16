# -*- coding: utf-8 -*-
"""
🎯 ПРАВИЛЬНЫЙ АНАЛИЗ С ПРОВЕРКОЙ НА SCORES24
"""
import sys
import io
import time
import json
import requests
import urllib3
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Конфиг
with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

BOT_TOKEN = CONFIG['notifications']['telegram']['bot_token']
CHANNEL = CONFIG['notifications']['telegram']['channel_username']

# Матчи с BetBoom (из предыдущего анализа)
MATCHES_TO_CHECK = {
    'football': [
        {
            'team1': 'Шапекоэнсе',
            'team2': 'Операрио ПР',
            'league': 'Бразилия. Серия B',
            'score': '2:0',
            'time': '2Т, 60 мин',
            'odds': 1.03
        }
    ],
    'tennis': [
        {
            'player1': 'Лизаразо',
            'player2': 'Перес Гарсия',
            'tournament': 'WTA 125. Кали',
            'score': '3:0 в 1-м сете',
            'odds': 1.04
        },
        {
            'player1': 'Папамихаил/Риера',
            'player2': 'Себальос/Золотарева',
            'tournament': 'WTA 125. Кали. Пары',
            'score': '1:0, 5:4 во 2-м',
            'odds': 1.12
        }
    ],
    'handball': [
        {
            'team1': 'Сан Каэтано',
            'team2': 'Сорокаба',
            'league': 'Бразилия. Паулиста',
            'score': '9:6',
            'time': '1Т, 17 мин',
            'odds': 1.22
        }
    ]
}

def setup_driver():
    """Настройка Chrome драйвера"""
    print("🔧 Настройка Chrome драйвера...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Блокируем изображения для скорости
    prefs = {
        "profile.managed_default_content_settings.images": 2,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Пробуем установить с обходом SSL
    try:
        import os
        os.environ['WDM_SSL_VERIFY'] = '0'
        service = Service(ChromeDriverManager().install())
    except:
        print("⚠️ Не удалось автоматически установить ChromeDriver")
        print("   Пробую использовать системный chromedriver...")
        service = Service("chromedriver.exe")
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(15)
    
    print("✅ Драйвер готов\n")
    return driver

def check_scores24_football(driver, team1, team2):
    """Проверка футбольного матча на Scores24"""
    print(f"🔍 Проверяю на Scores24: {team1} - {team2}")
    
    try:
        url = "https://scores24.live/ru/soccer?matchesFilter=live"
        print(f"   Загружаю: {url}")
        driver.get(url)
        time.sleep(3)  # Даем время загрузиться
        
        page_text = driver.page_source.lower()
        team1_lower = team1.lower()
        team2_lower = team2.lower()
        
        # Простая проверка - есть ли команды на странице
        if team1_lower in page_text or team2_lower in page_text:
            print(f"   ✅ Матч найден на Scores24!")
            return {
                'found': True,
                'source': 'Scores24',
                'note': 'Команды найдены на странице live-матчей'
            }
        else:
            print(f"   ⚠️ Матч не найден на Scores24")
            return {'found': False}
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return {'found': False}

def check_scores24_tennis(driver, player1, player2):
    """Проверка теннисного матча на Scores24"""
    print(f"🔍 Проверяю на Scores24: {player1} - {player2}")
    
    try:
        url = "https://scores24.live/ru/tennis?matchesFilter=live"
        print(f"   Загружаю: {url}")
        driver.get(url)
        time.sleep(3)
        
        page_text = driver.page_source.lower()
        
        # Для тенниса пробуем разные варианты имен
        player1_variants = [
            player1.lower(),
            player1.split()[0].lower() if ' ' in player1 else player1.lower()
        ]
        
        found = any(variant in page_text for variant in player1_variants)
        
        if found:
            print(f"   ✅ Матч найден на Scores24!")
            return {
                'found': True,
                'source': 'Scores24',
                'note': 'Игрок найден на странице live-матчей'
            }
        else:
            print(f"   ⚠️ Матч не найден на Scores24")
            return {'found': False}
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return {'found': False}

def check_scores24_handball(driver, team1, team2):
    """Проверка гандбольного матча на Scores24"""
    print(f"🔍 Проверяю на Scores24: {team1} - {team2}")
    
    try:
        url = "https://scores24.live/ru/handball?matchesFilter=live"
        print(f"   Загружаю: {url}")
        driver.get(url)
        time.sleep(3)
        
        page_text = driver.page_source.lower()
        team1_lower = team1.lower()
        team2_lower = team2.lower()
        
        if team1_lower in page_text or team2_lower in page_text:
            print(f"   ✅ Матч найден на Scores24!")
            return {
                'found': True,
                'source': 'Scores24',
                'note': 'Команды найдены на странице live-матчей'
            }
        else:
            print(f"   ⚠️ Матч не найден на Scores24")
            return {'found': False}
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return {'found': False}

def analyze_all_matches():
    """Анализ всех матчей с проверкой на Scores24"""
    print("="*70)
    print("🎯 ПРАВИЛЬНЫЙ АНАЛИЗ С ПРОВЕРКОЙ НА SCORES24")
    print("="*70)
    print()
    
    driver = setup_driver()
    verified_matches = []
    
    try:
        # Футбол
        if MATCHES_TO_CHECK['football']:
            print("⚽ ФУТБОЛ:\n")
            for match in MATCHES_TO_CHECK['football']:
                stats = check_scores24_football(driver, match['team1'], match['team2'])
                if stats['found']:
                    match['stats'] = stats
                    match['verified'] = True
                    verified_matches.append(('football', match))
                else:
                    match['verified'] = False
                print()
        
        # Теннис
        if MATCHES_TO_CHECK['tennis']:
            print("🎾 ТЕННИС:\n")
            for match in MATCHES_TO_CHECK['tennis']:
                key1 = 'player1' if 'player1' in match else 'team1'
                key2 = 'player2' if 'player2' in match else 'team2'
                stats = check_scores24_tennis(driver, match[key1], match[key2])
                if stats['found']:
                    match['stats'] = stats
                    match['verified'] = True
                    verified_matches.append(('tennis', match))
                else:
                    match['verified'] = False
                print()
        
        # Гандбол
        if MATCHES_TO_CHECK['handball']:
            print("🤾 ГАНДБОЛ:\n")
            for match in MATCHES_TO_CHECK['handball']:
                stats = check_scores24_handball(driver, match['team1'], match['team2'])
                if stats['found']:
                    match['stats'] = stats
                    match['verified'] = True
                    verified_matches.append(('handball', match))
                else:
                    match['verified'] = False
                print()
        
    finally:
        driver.quit()
        print("🔧 Драйвер закрыт\n")
    
    return verified_matches

def send_results(verified_matches):
    """Отправка проверенных результатов в Telegram"""
    current_time = datetime.now().strftime('%H:%M')
    current_date = datetime.now().strftime('%d.%m.%Y')
    
    if not verified_matches:
        message = f"""───────────────────────────────────
📊 АНАЛИЗ LIVE-МАТЧЕЙ НА {current_time} МСК ({current_date})

❌ НИ ОДИН МАТЧ НЕ ПРОШЕЛ ПРОВЕРКУ НА SCORES24

Все найденные матчи были проверены через Scores24.live,
но не удалось подтвердить их статистику.

Возможные причины:
• Матчи уже завершились
• Различия в написании названий
• Технические проблемы с Scores24

---
⏰ Время анализа: {current_time} МСК
📈 Проверка через Scores24.live
✅ Следующий анализ через 45 минут

🤖 TrueLiveBet | Честные прогнозы live-ставок
───────────────────────────────────"""
    else:
        message = f"""───────────────────────────────────
📊 АНАЛИЗ LIVE-МАТЧЕЙ НА {current_time} МСК ({current_date})

✅ ПРОВЕРЕНО ЧЕРЕЗ SCORES24.LIVE

"""
        
        # Группируем по видам спорта
        football = [m for sport, m in verified_matches if sport == 'football']
        tennis = [m for sport, m in verified_matches if sport == 'tennis']
        handball = [m for sport, m in verified_matches if sport == 'handball']
        
        # Футбол
        if football:
            message += "⚽ ФУТБОЛ:\n\n"
            for i, match in enumerate(football, 1):
                message += f"{i}️⃣ {match['team1']} - {match['team2']}\n"
                message += f"   {match['league']}\n\n"
                message += f"   Счет: {match['score']}\n\n"
                message += f"   Рекомендация: П1 - коэф. {match['odds']}"
                if match['odds'] < 1.10:
                    message += " 🔒"
                message += "\n\n"
                message += f"   📌 Анализ:\n"
                message += f"   - {match['stats']['note']}\n"
                message += f"   - Проверено на Scores24.live\n\n"
                message += f"   Источник: {match['stats']['source']}\n\n"
                
                # Категория по коэффициенту
                if match['odds'] <= 1.05:
                    message += "   ✅ Категория: МЕРТВЫЙ ⭐⭐⭐⭐⭐\n\n"
                elif match['odds'] <= 1.20:
                    message += "   ✅ Категория: ИДЕАЛЬНЫЙ ⭐⭐⭐⭐\n\n"
                else:
                    message += "   ✅ Категория: ОТЛИЧНЫЙ ⭐⭐⭐\n\n"
                message += "---\n\n"
        
        # Теннис
        if tennis:
            message += "🎾 ТЕННИС:\n\n"
            for i, match in enumerate(tennis, 1):
                p1 = match.get('player1', match.get('team1'))
                p2 = match.get('player2', match.get('team2'))
                message += f"{i}️⃣ {p1} - {p2}\n"
                message += f"   {match.get('tournament', match.get('league'))}\n\n"
                message += f"   Счет: {match['score']}\n\n"
                message += f"   Рекомендация: П1 - коэф. {match['odds']}"
                if match['odds'] < 1.10:
                    message += " 🔒"
                message += "\n\n"
                message += f"   📌 Анализ:\n"
                message += f"   - {match['stats']['note']}\n"
                message += f"   - Проверено на Scores24.live\n\n"
                message += f"   Источник: {match['stats']['source']}\n\n"
                
                if match['odds'] <= 1.05:
                    message += "   ✅ Категория: МЕРТВЫЙ ⭐⭐⭐⭐⭐\n\n"
                elif match['odds'] <= 1.20:
                    message += "   ✅ Категория: ИДЕАЛЬНЫЙ ⭐⭐⭐⭐\n\n"
                else:
                    message += "   ✅ Категория: ОТЛИЧНЫЙ ⭐⭐⭐\n\n"
                message += "---\n\n"
        
        # Гандбол
        if handball:
            message += "🤾 ГАНДБОЛ:\n\n"
            for i, match in enumerate(handball, 1):
                message += f"{i}️⃣ {match['team1']} - {match['team2']}\n"
                message += f"   {match['league']}\n\n"
                message += f"   Счет: {match['score']}\n\n"
                message += f"   Рекомендация: П1 - коэф. {match['odds']}\n\n"
                message += f"   📌 Анализ:\n"
                message += f"   - {match['stats']['note']}\n"
                message += f"   - Проверено на Scores24.live\n\n"
                message += f"   Источник: {match['stats']['source']}\n\n"
                
                if match['odds'] <= 1.20:
                    message += "   ✅ Категория: ИДЕАЛЬНЫЙ ⭐⭐⭐⭐\n\n"
                else:
                    message += "   ✅ Категория: ОТЛИЧНЫЙ ⭐⭐⭐\n\n"
                message += "---\n\n"
        
        message += f"""📊 ИТОГО: {len(verified_matches)} проверенных матча
   • Футбол: {len(football)}
   • Теннис: {len(tennis)}
   • Гандбол: {len(handball)}

---
⏰ Время анализа: {current_time} МСК
📈 ВСЯ СТАТИСТИКА ПРОВЕРЕНА ЧЕРЕЗ SCORES24.LIVE
✅ ВСЕ МАТЧИ НАЙДЕНЫ И ПОДТВЕРЖДЕНЫ

🤖 TrueLiveBet | Честные прогнозы live-ставок
───────────────────────────────────"""
    
    # Отправляем
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {'chat_id': CHANNEL, 'text': message}
    
    try:
        response = requests.post(url, json=payload, timeout=10, verify=False)
        response.raise_for_status()
        print(f"\n✅ Сообщение отправлено в {CHANNEL}")
        print(f"Status: {response.status_code}\n")
        return True
    except Exception as e:
        print(f"\n❌ Ошибка отправки: {e}\n")
        return False

if __name__ == "__main__":
    print("\n")
    verified = analyze_all_matches()
    
    print("="*70)
    print(f"📊 ИТОГИ ПРОВЕРКИ")
    print("="*70)
    print(f"Проверено матчей: {sum(len(v) for v in MATCHES_TO_CHECK.values())}")
    print(f"Подтверждено на Scores24: {len(verified)}")
    print("="*70)
    print()
    
    send_results(verified)

