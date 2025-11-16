# -*- coding: utf-8 -*-
"""
ТЕСТОВЫЙ РЕЖИМ: Полный анализ с Selenium
"""
import time
import sys
import io
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Исправляем кодировку для Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def setup_browser():
    """Настройка браузера Selenium"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(20)
    return driver

def get_betboom_matches(driver):
    """Получить live-матчи с BetBoom"""
    matches = {
        'football': [],
        'tennis': [],
        'handball': []
    }
    
    print("\n📊 Получаю данные с BetBoom...")
    
    try:
        # ФУТБОЛ
        print("   ⚽ Футбол...")
        driver.get('https://betboom.ru/sport/football?period=all&type=live')
        time.sleep(3)
        
        # Извлекаем текст страницы
        page_text = driver.execute_script("return document.body.innerText;")
        
        # Простой парсинг (в реальном режиме нужно использовать селекторы)
        if 'live' in page_text.lower() or 'матч' in page_text.lower():
            matches['football'].append({
                'source': 'betboom',
                'data': f"Найдено текста: {len(page_text)} символов"
            })
            print(f"      ✅ Страница загружена ({len(page_text)} символов)")
        
        # ТЕННИС
        print("   🎾 Теннис...")
        driver.get('https://betboom.ru/sport/tennis?period=all&type=live')
        time.sleep(3)
        
        page_text = driver.execute_script("return document.body.innerText;")
        if 'live' in page_text.lower():
            matches['tennis'].append({
                'source': 'betboom',
                'data': f"Найдено текста: {len(page_text)} символов"
            })
            print(f"      ✅ Страница загружена ({len(page_text)} символов)")
        
    except Exception as e:
        print(f"   ❌ Ошибка BetBoom: {e}")
    
    return matches

def get_flashscore_statistics(driver):
    """Получить статистику с Flashscore"""
    stats = []
    
    print("\n📈 Получаю статистику с Flashscore...")
    
    try:
        # Пробуем главную страницу
        driver.get('https://www.flashscorekz.com/')
        time.sleep(3)
        
        # Извлекаем live-матчи через JavaScript
        js_script = """
        var matches = [];
        var allText = document.body.innerText || document.body.textContent;
        return allText;
        """
        
        text_data = driver.execute_script(js_script)
        
        if text_data and len(text_data) > 1000:
            print(f"   ✅ Flashscore загружен: {len(text_data)} символов")
            
            # Ищем признаки live-матчей
            if 'live' in text_data.lower():
                stats.append({
                    'source': 'flashscore',
                    'size': len(text_data),
                    'has_live': True
                })
                print("   ✅ Найдены LIVE элементы")
            else:
                print("   ⚠️ LIVE элементы не найдены")
        else:
            print("   ❌ Недостаточно данных")
            
    except Exception as e:
        print(f"   ❌ Ошибка Flashscore: {e}")
    
    return stats

def analyze_matches(betboom_data, flashscore_stats):
    """Анализ матчей по чеклистам"""
    print("\n🔍 Анализирую матчи...")
    
    results = []
    
    # Проверяем наличие данных
    has_betboom = any(len(v) > 0 for v in betboom_data.values())
    has_flashscore = len(flashscore_stats) > 0
    
    print(f"   BetBoom данные: {'✅' if has_betboom else '❌'}")
    print(f"   Flashscore данные: {'✅' if has_flashscore else '❌'}")
    
    if has_betboom and has_flashscore:
        results.append({
            'status': 'success',
            'message': 'Данные получены с обоих источников',
            'betboom_sports': list(betboom_data.keys()),
            'flashscore_size': flashscore_stats[0]['size'] if flashscore_stats else 0
        })
        print("   ✅ Анализ возможен")
    else:
        results.append({
            'status': 'insufficient_data',
            'message': 'Недостаточно данных для анализа'
        })
        print("   ❌ Недостаточно данных")
    
    return results

def generate_telegram_message(analysis_results):
    """Генерация сообщения для Telegram"""
    now = datetime.now().strftime('%H:%M')
    
    message = f"🧠 ИИ-АНАЛИЗ LIVE • {now} МСК • ТЕСТОВЫЙ РЕЖИМ\n\n"
    message += "═" * 40 + "\n\n"
    
    if analysis_results and analysis_results[0]['status'] == 'success':
        message += "✅ ТЕСТ УСПЕШЕН!\n\n"
        message += "📊 ДАННЫЕ ПОЛУЧЕНЫ:\n"
        message += f"• BetBoom: {', '.join(analysis_results[0]['betboom_sports'])}\n"
        message += f"• Flashscore: {analysis_results[0]['flashscore_size']:,} символов\n\n"
        message += "🎯 СЛЕДУЮЩИЙ ШАГ:\n"
        message += "Интеграция парсинга конкретных матчей\n"
        message += "и применения чеклистов для каждого спорта.\n"
    else:
        message += "⚠️ ТЕХНИЧЕСКИЕ ПРОБЛЕМЫ\n\n"
        message += "Не удалось получить данные со всех источников.\n"
        message += "Продолжаем работу над стабилизацией подключения.\n"
    
    message += "\n" + "═" * 40 + "\n\n"
    message += "💡 Напоминаем: Подписка 500₽/неделя\n"
    message += "📞 @TrueLiveBet_Admin для вопросов\n"
    message += "💬 Обратная связь: пишите личные сообщения"
    
    return message

def main():
    """Основная функция тестового анализа"""
    print("=" * 50)
    print("🚀 ТЕСТОВЫЙ РЕЖИМ: Анализ с Selenium")
    print("=" * 50)
    
    driver = None
    
    try:
        # 1. Настройка браузера
        print("\n[1/5] Настройка браузера...")
        driver = setup_browser()
        print("✅ Браузер готов")
        
        # 2. Получение данных с BetBoom
        print("\n[2/5] Получение данных с BetBoom...")
        betboom_data = get_betboom_matches(driver)
        print(f"✅ Получено: {sum(len(v) for v in betboom_data.values())} источников")
        
        # 3. Получение статистики с Flashscore
        print("\n[3/5] Получение статистики с Flashscore...")
        flashscore_stats = get_flashscore_statistics(driver)
        print(f"✅ Получено: {len(flashscore_stats)} источников статистики")
        
        # 4. Анализ
        print("\n[4/5] Анализ данных...")
        analysis_results = analyze_matches(betboom_data, flashscore_stats)
        print(f"✅ Анализ завершен: {len(analysis_results)} результатов")
        
        # 5. Генерация сообщения
        print("\n[5/5] Генерация сообщения для Telegram...")
        telegram_message = generate_telegram_message(analysis_results)
        
        # Сохранение результатов
        with open('current_live_analysis_mcp.txt', 'w', encoding='utf-8') as f:
            f.write(telegram_message)
        print("✅ Сообщение сохранено в current_live_analysis_mcp.txt")
        
        # Сохранение подробных данных
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'betboom_data': betboom_data,
            'flashscore_stats': flashscore_stats,
            'analysis_results': analysis_results
        }
        
        with open('test_analysis_results.json', 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        print("✅ Детальные данные сохранены в test_analysis_results.json")
        
        print("\n" + "=" * 50)
        print("✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
        print("=" * 50)
        print("\n📄 СООБЩЕНИЕ ДЛЯ TELEGRAM:\n")
        print(telegram_message)
        
        return True
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if driver:
            print("\n🔒 Закрываю браузер...")
            driver.quit()
            print("✅ Браузер закрыт")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

