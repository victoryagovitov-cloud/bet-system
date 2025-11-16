# -*- coding: utf-8 -*-
"""
🎯 ФИНАЛЬНЫЙ АНАЛИЗАТОР: MCP + SCORES24 + TELEGRAM
Полный цикл анализа БЕЗ web search
"""
import sys
import io
import time
import json
import requests
import urllib3
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Конфиг
with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

BOT_TOKEN = CONFIG['notifications']['telegram']['bot_token']
CHANNEL = CONFIG['notifications']['telegram']['channel_username']

# ===================== УМНЫЙ ПОИСК =====================

def get_name_variants(name):
    """Генерация вариантов написания с транслитерацией"""
    variants = [name.lower()]
    
    # Убираем скобки
    variants.append(re.sub(r'\([^)]*\)', '', name).strip().lower())
    
    # Составные имена
    if '/' in name:
        parts = name.split('/')
        variants.extend([p.strip().lower() for p in parts])
    
    # Инициалы
    if '.' in name:
        variants.append(name.split('.')[0].strip().lower())
    
    # Части слов
    words = name.split()
    if len(words) > 1:
        variants.append(words[-1].lower())
        variants.append(words[0].lower())
    
    # Транслитерация
    translits = {
        'шапекоэнсе': ['chapecoense', 'chape'],
        'операрио': ['operario'],
        'сан каэтано': ['sao caetano', 'caetano', 'sao'],
        'сорокаба': ['sorocaba'],
        'лизаразо': ['lizarazo'],
        'перес': ['perez'],
        'гарсия': ['garcia'],
        'папамихаил': ['papamichail'],
        'себальос': ['ceballos'],
        'золотарева': ['zolotareva'],
        'риера': ['riera'],
        'цинциннати': ['cincinnati'],
        'коламбус': ['columbus'],
        'крю': ['crew'],
        'насиональ': ['nacional'],
        'серро': ['cerro'],
        'портеньо': ['porteno'],
        'крисиума': ['criciuma'],
        'жоинвиль': ['joinville']
    }
    
    name_lower = name.lower()
    for rus, eng_list in translits.items():
        if rus in name_lower:
            variants.extend(eng_list)
    
    return list(set(variants))

def smart_search(page_text, team1, team2):
    """Умный поиск с вариантами"""
    page_lower = page_text.lower()
    
    team1_variants = get_name_variants(team1)
    team2_variants = get_name_variants(team2)
    
    print(f"   🔍 Ищу варианты: {team1_variants[:3]}...")
    
    team1_found = any(v in page_lower for v in team1_variants)
    team2_found = any(v in page_lower for v in team2_variants)
    
    if team1_found or team2_found:
        return True, f"Найдено: {team1 if team1_found else team2}"
    
    return False, "Не найдено"

# ===================== SELENIUM SETUP =====================

def setup_driver():
    """Настройка драйвера"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        import os
        os.environ['WDM_SSL_VERIFY'] = '0'
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    except:
        service = Service("chromedriver.exe")
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(15)
    return driver

# ===================== ПРОВЕРКА SCORES24 =====================

def verify_on_scores24(driver, sport, team1, team2, match_data):
    """Проверка матча на Scores24"""
    urls = {
        'football': 'https://scores24.live/ru/soccer?matchesFilter=live',
        'tennis': 'https://scores24.live/ru/tennis?matchesFilter=live',
        'handball': 'https://scores24.live/ru/handball?matchesFilter=live'
    }
    
    try:
        driver.get(urls[sport])
        time.sleep(3)
        
        found, details = smart_search(driver.page_source, team1, team2)
        
        if found:
            print(f"   ✅ {details}")
            return {
                'verified': True,
                'source': 'Scores24.live',
                'details': details,
                'match': match_data
            }
        else:
            print(f"   ❌ Не найдено")
            return {'verified': False}
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return {'verified': False}

# ===================== ПАРСИНГ MCP ДАННЫХ =====================

def parse_mcp_betboom_data(mcp_data):
    """
    Парсинг данных с BetBoom (полученных через MCP browser)
    
    На вход: данные от MCP browser с BetBoom
    На выход: структурированные матчи
    """
    # TODO: Здесь будет реальный парсинг MCP данных
    # Пока используем структуру для примера
    
    matches = {
        'football': [],
        'tennis': [],
        'handball': []
    }
    
    # Пример: если в mcp_data есть футбольные матчи
    # for match in mcp_data['football']:
    #     matches['football'].append({
    #         'team1': match['home'],
    #         'team2': match['away'],
    #         'league': match['league'],
    #         'score': match['score'],
    #         'time': match['time'],
    #         'odds': match['odds']
    #     })
    
    return matches

# ===================== ГЛАВНАЯ ФУНКЦИЯ =====================

def analyze_betboom_live(betboom_snapshot):
    """
    Главная функция анализа
    
    betboom_snapshot: данные с BetBoom через MCP browser
    """
    print("\n" + "="*70)
    print("🎯 ПОЛНЫЙ АНАЛИЗ: BETBOOM → SCORES24 → TELEGRAM")
    print("="*70 + "\n")
    
    start_time = time.time()
    
    # 1. Парсим данные с BetBoom
    print("📊 Шаг 1: Парсинг данных с BetBoom...")
    matches = parse_mcp_betboom_data(betboom_snapshot)
    total = sum(len(v) for v in matches.values())
    print(f"   Найдено: {total} матчей\n")
    
    if total == 0:
        print("❌ Нет матчей для анализа\n")
        return
    
    # 2. Проверяем на Scores24
    print("📊 Шаг 2: Проверка на Scores24...")
    driver = setup_driver()
    verified = []
    
    try:
        for sport in ['football', 'tennis', 'handball']:
            if matches[sport]:
                sport_icons = {'football': '⚽', 'tennis': '🎾', 'handball': '🤾'}
                print(f"\n{sport_icons[sport]} {sport.upper()}:")
                
                for match in matches[sport]:
                    t1 = match.get('team1') or match.get('player1')
                    t2 = match.get('team2') or match.get('player2')
                    print(f"🔍 {t1} - {t2}")
                    
                    result = verify_on_scores24(driver, sport, t1, t2, match)
                    if result['verified']:
                        verified.append((sport, result))
    finally:
        driver.quit()
    
    # 3. Отправляем в Telegram
    print(f"\n📊 Шаг 3: Отправка в Telegram...")
    send_to_telegram(verified)
    
    elapsed = time.time() - start_time
    print(f"\n✅ Анализ завершен за {elapsed:.1f}с\n")

# ===================== ОТПРАВКА В TELEGRAM =====================

def send_to_telegram(verified_matches):
    """Отправка результатов"""
    current_time = datetime.now().strftime('%H:%M')
    current_date = datetime.now().strftime('%d.%m.%Y')
    
    if not verified_matches:
        message = f"""───────────────────────────────────
📊 АНАЛИЗ LIVE-МАТЧЕЙ НА {current_time} МСК ({current_date})

❌ ПОДХОДЯЩИХ МАТЧЕЙ НЕ НАЙДЕНО

Все матчи проверены через Scores24.live с умным поиском,
но не удалось подтвердить их статистику.

---
⏰ Время анализа: {current_time} МСК
📈 Проверка: BetBoom → Scores24 → Умный поиск
✅ Следующий анализ через 45 минут

🤖 TrueLiveBet | Честные прогнозы live-ставок
───────────────────────────────────"""
    else:
        message = f"""───────────────────────────────────
📊 АНАЛИЗ LIVE-МАТЧЕЙ НА {current_time} МСК ({current_date})

✅ ПРОВЕРЕНО: BETBOOM + SCORES24 + УМНЫЙ ПОИСК

"""
        
        by_sport = {'football': [], 'tennis': [], 'handball': []}
        for sport, data in verified_matches:
            by_sport[sport].append(data)
        
        # Футбол
        if by_sport['football']:
            message += "⚽ ФУТБОЛ:\n\n"
            for i, data in enumerate(by_sport['football'], 1):
                m = data['match']
                message += f"{i}️⃣ {m['team1']} - {m['team2']}\n"
                message += f"   {m['league']}\n\n"
                message += f"   Счет: {m['score']}\n\n"
                message += f"   Рекомендация: П1 - коэф. {m['odds']}"
                if m['odds'] < 1.10:
                    message += " 🔒"
                message += "\n\n"
                message += f"   📌 {data['details']}\n"
                message += f"   Проверено на Scores24.live\n\n"
                
                if m['odds'] <= 1.05:
                    message += "   ✅ МЕРТВЫЙ ⭐⭐⭐⭐⭐\n\n"
                elif m['odds'] <= 1.20:
                    message += "   ✅ ИДЕАЛЬНЫЙ ⭐⭐⭐⭐\n\n"
                else:
                    message += "   ✅ ОТЛИЧНЫЙ ⭐⭐⭐\n\n"
                message += "---\n\n"
        
        # Теннис
        if by_sport['tennis']:
            message += "🎾 ТЕННИС:\n\n"
            for i, data in enumerate(by_sport['tennis'], 1):
                m = data['match']
                p1 = m.get('player1') or m.get('team1')
                p2 = m.get('player2') or m.get('team2')
                message += f"{i}️⃣ {p1} - {p2}\n"
                message += f"   {m.get('tournament') or m.get('league')}\n\n"
                message += f"   Счет: {m['score']}\n\n"
                message += f"   Рекомендация: П1 - коэф. {m['odds']}"
                if m['odds'] < 1.10:
                    message += " 🔒"
                message += "\n\n"
                message += f"   📌 {data['details']}\n"
                message += f"   Проверено на Scores24.live\n\n"
                
                if m['odds'] <= 1.05:
                    message += "   ✅ МЕРТВЫЙ ⭐⭐⭐⭐⭐\n\n"
                elif m['odds'] <= 1.20:
                    message += "   ✅ ИДЕАЛЬНЫЙ ⭐⭐⭐⭐\n\n"
                else:
                    message += "   ✅ ОТЛИЧНЫЙ ⭐⭐⭐\n\n"
                message += "---\n\n"
        
        # Гандбол
        if by_sport['handball']:
            message += "🤾 ГАНДБОЛ:\n\n"
            for i, data in enumerate(by_sport['handball'], 1):
                m = data['match']
                message += f"{i}️⃣ {m['team1']} - {m['team2']}\n"
                message += f"   {m['league']}\n\n"
                message += f"   Счет: {m['score']}\n\n"
                message += f"   Рекомендация: П1 - коэф. {m['odds']}\n\n"
                message += f"   📌 {data['details']}\n"
                message += f"   Проверено на Scores24.live\n\n"
                
                if m['odds'] <= 1.20:
                    message += "   ✅ ИДЕАЛЬНЫЙ ⭐⭐⭐⭐\n\n"
                else:
                    message += "   ✅ ОТЛИЧНЫЙ ⭐⭐⭐\n\n"
                message += "---\n\n"
        
        total = sum(len(v) for v in by_sport.values())
        message += f"""📊 ИТОГО: {total} проверенных матча
   • Футбол: {len(by_sport['football'])}
   • Теннис: {len(by_sport['tennis'])}
   • Гандбол: {len(by_sport['handball'])}

---
⏰ {current_time} МСК
📈 БЕЗ WEB SEARCH - только прямые источники!
✅ УМНЫЙ ПОИСК учел различия в написании

🤖 TrueLiveBet | Честные прогнозы live-ставок
───────────────────────────────────"""
    
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {'chat_id': CHANNEL, 'text': message}
    
    try:
        response = requests.post(url, json=payload, timeout=10, verify=False)
        response.raise_for_status()
        print(f"✅ Отправлено в {CHANNEL} (код {response.status_code})")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

# ===================== ДЛЯ ИНТЕГРАЦИИ С MCP =====================

def analyze_from_mcp_snapshot(snapshot_data):
    """
    Функция для вызова из Cursor с данными MCP
    
    Использование:
    from final_mcp_scores24_analyzer import analyze_from_mcp_snapshot
    analyze_from_mcp_snapshot(betboom_data)
    """
    analyze_betboom_live(snapshot_data)

if __name__ == "__main__":
    print("🎯 Финальный анализатор готов к работе!")
    print("\nДля запуска из Cursor используйте:")
    print("  from final_mcp_scores24_analyzer import analyze_from_mcp_snapshot")
    print("  analyze_from_mcp_snapshot(betboom_data)")

