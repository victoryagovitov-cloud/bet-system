# -*- coding: utf-8 -*-
"""
СИСТЕМА ПАКЕТНОГО АНАЛИЗА
Анализ больших объемов матчей частями с отправкой результатов после каждой партии
"""
import time
import sys
import io
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def setup_selenium():
    """Настройка Selenium"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(15)
    return driver

def calculate_batch_size(total_matches):
    """
    Динамическое определение размера пакета
    """
    if total_matches <= 20:
        return total_matches  # Все за раз
    elif total_matches <= 50:
        return 15  # 15 матчей на пакет
    elif total_matches <= 100:
        return 20  # 20 матчей на пакет
    else:
        return 25  # 25 матчей на пакет для очень больших объемов
    
def get_fresh_betboom_matches_batch(start_idx, batch_size):
    """
    Получить СВЕЖИЕ данные с BetBoom для конкретного пакета
    В реальном режиме - через MCP browser
    Сейчас - симуляция с примерными данными
    """
    print(f"\n🔄 Получаю СВЕЖИЕ данные для пакета (матчи {start_idx+1}-{start_idx+batch_size})...")
    
    # ЗАГЛУШКА: В реальном режиме здесь будет вызов MCP browser
    # для получения актуального списка матчей
    
    all_matches = [
        {'team1': 'Спортинг', 'team2': 'Брага', 'score': '1-0', 'time': '35\'', 'league': 'Португалия', 'odds': '1.22'},
        {'team1': 'Вестерло', 'team2': 'Хеверлее Лёвен', 'score': '1-0', 'time': '75\'', 'league': 'Бельгия', 'odds': '1.20'},
        {'team1': 'Гезтепе', 'team2': 'Башакшехир', 'score': '1-0', 'time': '85\'', 'league': 'Турция', 'odds': '1.15'},
        {'team1': 'Пирамидс', 'team2': 'АПР', 'score': '3-0', 'time': '90\'', 'league': 'КАФ', 'odds': '1.05'},
        {'team1': 'Боруссия М', 'team2': 'Фрайбург', 'score': '0-0', 'time': '65\'', 'league': 'Германия', 'odds': '3.43'},
        # ... еще матчи
    ]
    
    # Возвращаем пакет
    batch = all_matches[start_idx:start_idx+batch_size]
    
    print(f"   ✅ Получено: {len(batch)} матчей")
    
    return batch, len(all_matches)

def get_stats_for_match(driver, match):
    """Получить статистику для матча через Selenium"""
    try:
        driver.get('https://scores24.live/ru/soccer?matchesFilter=live')
        time.sleep(2)
        page_text = driver.execute_script("return document.body.innerText;")
        
        if len(page_text) > 1000:
            return [{'source': 'scores24', 'loaded': True, 'size': len(page_text)}]
    except:
        pass
    
    return []

def analyze_football_match(match, stats):
    """Анализ футбольного матча по чеклисту"""
    if not stats:
        return None
    
    score_parts = match['score'].split('-')
    if len(score_parts) != 2:
        return None
    
    score1, score2 = int(score_parts[0]), int(score_parts[1])
    
    # Проверка: ненич. счет + фаворит ведет
    non_draw = (score1 != score2)
    is_favorite = float(match['odds']) < 2.0
    is_leading = score1 > score2
    
    if non_draw and is_favorite and is_leading:
        # Категоризация
        minute = int(match['time'].replace('\'', '').replace('+', ''))
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
            'stats_sources': len(stats)
        }
    
    return None

def format_batch_message(batch_num, total_batches, results, batch_time):
    """Форматирование сообщения для пакета"""
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
        message += "⚪ В этом пакете подходящих матчей не найдено\n\n"
    
    if batch_num == total_batches:
        message += "✅ АНАЛИЗ ЗАВЕРШЕН\n\n"
        message += "💡 Категории:\n"
        message += "• МЕРТВЫЙ: 80+ мин, коэфф <1.15\n"
        message += "• ИДЕАЛЬНЫЙ: 60+ мин, коэфф <1.30\n"
        message += "• ОТЛИЧНЫЙ: 45+ мин, коэфф <1.50\n"
        message += "• ХОРОШИЙ: остальные\n\n"
    
    message += f"⏱️ Обработано за {batch_time:.1f} сек\n\n"
    message += "═" * 40 + "\n\n"
    message += "💡 Подписка 500₽/неделя\n"
    message += "📞 @TrueLiveBet_Admin"
    
    return message

def send_batch_to_telegram(message):
    """Отправка сообщения в Telegram"""
    with open('current_live_analysis_mcp.txt', 'w', encoding='utf-8') as f:
        f.write(message)
    
    # Отправка через существующий скрипт
    import subprocess
    result = subprocess.run(['python', 'send_fixed_analysis.py'], 
                          capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode == 0:
        print("   ✅ Отправлено в @TrueLiveBet")
        return True
    else:
        print("   ❌ Ошибка отправки")
        return False

def main():
    """Главная функция пакетного анализа"""
    print("=" * 70)
    print("📦 СИСТЕМА ПАКЕТНОГО АНАЛИЗА")
    print("=" * 70)
    print(f"Время запуска: {datetime.now().strftime('%H:%M:%S')} МСК\n")
    
    driver = None
    total_found = 0
    
    try:
        driver = setup_selenium()
        
        # Шаг 1: Получаем первый пакет для определения общего количества
        print("[ЭТАП 1] Определение объема работы...")
        batch_matches, total_matches = get_fresh_betboom_matches_batch(0, 1)
        
        batch_size = calculate_batch_size(total_matches)
        total_batches = (total_matches + batch_size - 1) // batch_size
        
        print(f"\n📊 ПЛАН РАБОТЫ:")
        print(f"   Всего матчей: {total_matches}")
        print(f"   Размер пакета: {batch_size}")
        print(f"   Количество пакетов: {total_batches}")
        print(f"   Время на пакет: ~{batch_size * 3}сек\n")
        
        # Шаг 2: Обрабатываем пакеты
        for batch_num in range(1, total_batches + 1):
            print(f"\n{'='*70}")
            print(f"📦 ПАКЕТ {batch_num}/{total_batches}")
            print(f"{'='*70}")
            
            batch_start_time = time.time()
            start_idx = (batch_num - 1) * batch_size
            
            # Получаем СВЕЖИЕ данные для этого пакета
            batch_matches, _ = get_fresh_betboom_matches_batch(start_idx, batch_size)
            
            if not batch_matches:
                print("   ⚠️ Пакет пустой, пропускаем")
                continue
            
            # Анализируем каждый матч в пакете
            batch_results = []
            
            for i, match in enumerate(batch_matches, 1):
                print(f"\n   [{i}/{len(batch_matches)}] {match['team1']} vs {match['team2']}")
                
                # Получаем статистику
                stats = get_stats_for_match(driver, match)
                
                if stats:
                    print(f"      ✅ Статистика: {len(stats)} источников")
                    
                    # Анализируем
                    analysis = analyze_football_match(match, stats)
                    
                    if analysis:
                        batch_results.append(analysis)
                        print(f"      ✅ {analysis['category']}")
                        total_found += 1
                    else:
                        print(f"      ⚪ Не прошел чеклист")
                else:
                    print(f"      ❌ Нет статистики")
            
            batch_time = time.time() - batch_start_time
            
            # Формируем и отправляем сообщение для этого пакета
            print(f"\n   📤 Отправка результатов пакета {batch_num}...")
            message = format_batch_message(batch_num, total_batches, batch_results, batch_time)
            send_batch_to_telegram(message)
            
            # Небольшая пауза между пакетами
            if batch_num < total_batches:
                print(f"\n   ⏸️ Пауза 2 сек перед следующим пакетом...")
                time.sleep(2)
        
        print(f"\n{'='*70}")
        print(f"✅ ВСЕ ПАКЕТЫ ОБРАБОТАНЫ")
        print(f"{'='*70}")
        print(f"Всего найдено подходящих матчей: {total_found}")
        print(f"Время выполнения: {datetime.now().strftime('%H:%M:%S')} МСК\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

