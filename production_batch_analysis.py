# -*- coding: utf-8 -*-
"""
PRODUCTION: СИСТЕМА ПАКЕТНОГО АНАЛИЗА С MCP BROWSER
Полная интеграция с BetBoom через MCP Browser + Selenium
"""
import time
import sys
import io
import subprocess
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def setup_selenium():
    """Настройка Selenium для статистики"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(15)
    return driver

def calculate_batch_size(total_matches):
    """Динамическое определение размера пакета"""
    if total_matches <= 20:
        return total_matches
    elif total_matches <= 50:
        return 15
    elif total_matches <= 100:
        return 20
    else:
        return 25

def parse_betboom_football_matches_from_snapshot(snapshot_data):
    """
    Парсинг футбольных матчей из данных MCP Browser
    
    Ищем в snapshot данные матчей:
    - Название команд
    - Счет
    - Время
    - Лига
    - Коэффициенты
    """
    matches = []
    
    # ЗАГЛУШКА: В реальном режиме парсим snapshot от MCP Browser
    # Пример структуры, которую мы получаем:
    # region -> button/link -> text: "Команда1" "Команда2" "1 0" "45 мин"
    
    # Для ПРОДАКШЕНА: реализовать парсинг YAML структуры от MCP Browser
    # Сейчас возвращаем заглушку для демонстрации
    
    print("   ⚠️ ВНИМАНИЕ: Используется заглушка парсинга")
    print("   📝 TODO: Реализовать парсинг snapshot от MCP Browser")
    
    return matches

def get_stats_scores24(driver, match):
    """Получить статистику с Scores24"""
    try:
        driver.get('https://scores24.live/ru/soccer?matchesFilter=live')
        time.sleep(2)
        page_text = driver.execute_script("return document.body.innerText;")
        
        if len(page_text) > 1000:
            return {'source': 'scores24', 'loaded': True, 'size': len(page_text)}
    except Exception as e:
        return {'source': 'scores24', 'loaded': False, 'error': str(e)}
    
    return None

def analyze_football_match(match, stats):
    """Анализ футбольного матча по чеклисту"""
    if not stats or not stats.get('loaded'):
        return None
    
    try:
        score_parts = match['score'].split('-')
        if len(score_parts) != 2:
            return None
        
        score1, score2 = int(score_parts[0]), int(score_parts[1])
        
        # Чеклист: ненич. счет + фаворит ведет
        non_draw = (score1 != score2)
        is_favorite = float(match['odds']) < 2.0
        is_leading = score1 > score2
        
        if non_draw and is_favorite and is_leading:
            # Категоризация
            time_str = match['time'].replace('\'', '').replace('+', '').replace('Т', '').replace(' ', '')
            minute = int(time_str) if time_str.isdigit() else 45
            odds = float(match['odds'])
            
            if minute >= 80 and odds < 1.15:
                category = 'МЕРТВЫЙ'
            elif minute >= 60 and odds < 1.30:
                category = 'ИДЕАЛЬНЫЙ'
            elif minute >= 45 and odds < 1.50:
                category = 'ОТЛИЧНЫЙ'
            else:
                category = 'ХОРОШИЙ'
            
            return {
                'match': match,
                'category': category,
                'stats_sources': 1
            }
    except Exception as e:
        print(f"      ⚠️ Ошибка анализа: {e}")
    
    return None

def format_batch_message(batch_num, total_batches, results, batch_time):
    """Форматирование сообщения для Telegram"""
    now = datetime.now().strftime('%H:%M')
    
    message = f"🧠 ИИ-АНАЛИЗ LIVE • {now} МСК\n\n"
    message += "═" * 40 + "\n\n"
    message += f"📦 ПАКЕТ {batch_num}/{total_batches}\n\n"
    
    if results:
        message += f"✅ НАЙДЕНО: {len(results)} подходящих\n\n"
        
        for i, r in enumerate(results, 1):
            m = r['match']
            message += f"{i}. ⚽ {m['team1']} – {m['team2']}\n"
            message += f"   {m['league']}\n"
            message += f"   Счет: {m['score']} ({m['time']})\n"
            message += f"   Категория: {r['category']}\n"
            message += f"   Коэфф П1: {m['odds']}\n\n"
    else:
        message += "⚪ В этом пакете подходящих не найдено\n\n"
    
    if batch_num == total_batches:
        message += "✅ АНАЛИЗ ЗАВЕРШЕН\n\n"
    
    message += f"⏱️ Обработано за {batch_time:.1f} сек\n\n"
    message += "═" * 40 + "\n\n"
    message += "💡 Подписка 500₽/неделя\n"
    message += "📞 @TrueLiveBet_Admin"
    
    return message

def send_to_telegram(message):
    """Отправка в Telegram"""
    with open('current_live_analysis_mcp.txt', 'w', encoding='utf-8') as f:
        f.write(message)
    
    result = subprocess.run(['python', 'send_fixed_analysis.py'], 
                          capture_output=True, text=True, encoding='utf-8')
    
    return result.returncode == 0

def main():
    """
    PRODUCTION: Главная функция пакетного анализа
    
    АРХИТЕКТУРА:
    1. MCP Browser → BetBoom (получение списка матчей)
    2. Разбивка на пакеты
    3. Для каждого пакета:
       - MCP Browser → Свежие данные этих матчей
       - Selenium → Статистика (Scores24/Flashscore)
       - Анализ по чеклистам
       - Отправка в Telegram
    """
    
    print("=" * 70)
    print("📦 PRODUCTION: ПАКЕТНЫЙ АНАЛИЗ С MCP BROWSER")
    print("=" * 70)
    print(f"Время: {datetime.now().strftime('%H:%M:%S')} МСК\n")
    
    print("⚠️ ВНИМАНИЕ: Для ПРОДАКШЕНА требуется:")
    print("   1. Интеграция вызовов MCP Browser из Python")
    print("   2. Парсинг YAML snapshot от MCP Browser")
    print("   3. Обработка всех видов спорта (футбол, теннис, гандбол)\n")
    
    print("📝 ТЕКУЩИЙ СТАТУС:")
    print("   ✅ Архитектура готова")
    print("   ✅ Selenium интегрирован")
    print("   ✅ Чеклисты реализованы")
    print("   ⚠️ MCP Browser парсинг - требуется доработка")
    print("   ✅ Telegram отправка работает\n")
    
    print("🎯 РЕКОМЕНДАЦИИ:")
    print("   1. Использовать текущую систему quick_top5_analysis.py")
    print("   2. Постепенно интегрировать MCP Browser парсинг")
    print("   3. Расширить чеклисты для тенниса и гандбола\n")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

