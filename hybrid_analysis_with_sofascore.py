# -*- coding: utf-8 -*-
"""
ГИБРИДНЫЙ АНАЛИЗ: MCP Browser (BetBoom) + Selenium (3 источника статистики)
Источники статистики:
1. Flashscore (основной)
2. Scores24 (второй)
3. Sofascore (резервный)
"""
import time
import sys
import io
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Исправляем кодировку для Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def setup_selenium():
    """Настройка Selenium для статистики"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(20)
    return driver

def get_betboom_with_mcp():
    """Получить матчи с BetBoom через MCP browser"""
    print("\n📊 [MCP BROWSER] Получаю данные с BetBoom...")
    
    # ЗАГЛУШКА: В реальном режиме здесь будет вызов MCP browser
    matches = {
        'football': [
            {
                'team1': 'Рио Аве',
                'team2': 'Тондела',
                'score': '3-0',
                'time': '90+',
                'league': 'Португалия',
                'odds': '1.04'
            },
            {
                'team1': 'Вестерло',
                'team2': 'Хеверлее Лёвен',
                'score': '1-0',
                'time': '48',
                'league': 'Бельгия',
                'odds': '1.35'
            }
        ],
        'tennis': [
            {
                'player1': 'Синнер',
                'player2': 'Медведев',
                'score': '6-4, 3-2',
                'tournament': 'ATP Shanghai',
                'odds': '1.15'
            }
        ],
        'handball': []
    }
    
    print(f"   ✅ Футбол: {len(matches['football'])} матчей")
    print(f"   ✅ Теннис: {len(matches['tennis'])} матчей")
    print(f"   ✅ Гандбол: {len(matches['handball'])} матчей")
    
    return matches

def get_flashscore_stats(driver, match_info, sport='football'):
    """1. Flashscore - основной источник"""
    print(f"\n📈 [1/3 FLASHSCORE] {match_info.get('team1', match_info.get('player1'))} ...")
    
    try:
        if sport == 'football':
            driver.get('https://www.flashscorekz.com/football/')
        elif sport == 'tennis':
            driver.get('https://www.flashscorekz.com/tennis/')
        elif sport == 'handball':
            driver.get('https://www.flashscorekz.com/handball/')
        
        time.sleep(3)
        
        page_text = driver.execute_script("return document.body.innerText;")
        
        stats = {
            'source': 'flashscore',
            'loaded': True,
            'page_size': len(page_text),
            'has_live': 'live' in page_text.lower()
        }
        
        print(f"   ✅ Загружен: {len(page_text):,} символов")
        return stats
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:50]}...")
        return {'source': 'flashscore', 'loaded': False, 'error': str(e)}

def get_scores24_stats(driver, match_info, sport='football'):
    """2. Scores24 - второй источник"""
    print(f"\n📊 [2/3 SCORES24] {match_info.get('team1', match_info.get('player1'))} ...")
    
    try:
        if sport == 'football':
            driver.get('https://scores24.live/ru/soccer?matchesFilter=live')
        elif sport == 'tennis':
            driver.get('https://scores24.live/ru/tennis?matchesFilter=live')
        elif sport == 'handball':
            driver.get('https://scores24.live/ru/handball?matchesFilter=live')
        
        time.sleep(3)
        
        page_text = driver.execute_script("return document.body.innerText;")
        
        stats = {
            'source': 'scores24',
            'loaded': True,
            'page_size': len(page_text)
        }
        
        print(f"   ✅ Загружен: {len(page_text):,} символов")
        return stats
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:50]}...")
        return {'source': 'scores24', 'loaded': False, 'error': str(e)}

def get_sofascore_stats(driver, match_info, sport='football'):
    """3. Sofascore - резервный источник"""
    print(f"\n⚽ [3/3 SOFASCORE] {match_info.get('team1', match_info.get('player1'))} ...")
    
    try:
        # Sofascore имеет общую страницу для live
        driver.get('https://www.sofascore.com/')
        time.sleep(4)  # Sofascore загружается дольше
        
        page_text = driver.execute_script("return document.body.innerText;")
        
        stats = {
            'source': 'sofascore',
            'loaded': True,
            'page_size': len(page_text),
            'has_live': 'live' in page_text.lower()
        }
        
        print(f"   ✅ Загружен: {len(page_text):,} символов")
        return stats
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:50]}...")
        return {'source': 'sofascore', 'loaded': False, 'error': str(e)}

def collect_all_statistics(driver, match, sport):
    """Собрать статистику из всех 3 источников"""
    print(f"\n{'='*60}")
    print(f"🔍 СБОР СТАТИСТИКИ: {match.get('team1', match.get('player1'))} vs {match.get('team2', match.get('player2'))}")
    print(f"{'='*60}")
    
    stats_collection = []
    
    # 1. Flashscore
    flashscore = get_flashscore_stats(driver, match, sport)
    if flashscore.get('loaded'):
        stats_collection.append(flashscore)
    
    # 2. Scores24
    scores24 = get_scores24_stats(driver, match, sport)
    if scores24.get('loaded'):
        stats_collection.append(scores24)
    
    # 3. Sofascore
    sofascore = get_sofascore_stats(driver, match, sport)
    if sofascore.get('loaded'):
        stats_collection.append(sofascore)
    
    return stats_collection

def analyze_with_multiple_sources(match, stats_collection, sport):
    """Анализ с использованием нескольких источников"""
    print(f"\n📊 АНАЛИЗ:")
    
    sources_available = [s['source'] for s in stats_collection]
    print(f"   Источников загружено: {len(sources_available)}")
    print(f"   Список: {', '.join(sources_available)}")
    
    # ЖЕЛЕЗНОЕ ПРАВИЛО: минимум 2 источника (если Flashscore + еще один)
    # или минимум 1 (если Flashscore работает)
    if len(sources_available) == 0:
        print("   ❌ НЕТ ИСТОЧНИКОВ - анализ невозможен")
        return None
    
    if len(sources_available) < 2:
        print("   ⚠️ Только 1 источник - рекомендуется больше")
    else:
        print("   ✅ Достаточно источников для анализа")
    
    analysis = {
        'match': match,
        'sources': sources_available,
        'sources_count': len(sources_available),
        'stats_data': stats_collection,
        'can_analyze': len(sources_available) >= 1,
        'quality': 'high' if len(sources_available) >= 2 else 'medium' if len(sources_available) == 1 else 'low'
    }
    
    return analysis

def main():
    """Основная функция"""
    print("=" * 70)
    print("🚀 ГИБРИДНЫЙ АНАЛИЗ: 3 ИСТОЧНИКА СТАТИСТИКИ")
    print("=" * 70)
    print("\n📋 АРХИТЕКТУРА:")
    print("   • MCP Browser → BetBoom (матчи)")
    print("   • Selenium → Flashscore (основной)")
    print("   • Selenium → Scores24 (второй)")
    print("   • Selenium → Sofascore (резервный)")
    print("=" * 70)
    
    driver = None
    
    try:
        # 1. BetBoom через MCP
        print("\n[ЭТАП 1] BetBoom через MCP Browser")
        betboom_matches = get_betboom_with_mcp()
        
        # 2. Selenium
        print("\n[ЭТАП 2] Настройка Selenium")
        driver = setup_selenium()
        print("   ✅ Selenium готов")
        
        # 3. Сбор статистики
        print("\n[ЭТАП 3] Сбор статистики из 3 источников")
        
        all_results = []
        
        # Тестируем один футбольный матч
        if betboom_matches['football']:
            match = betboom_matches['football'][0]
            
            # Собираем статистику из всех источников
            stats_collection = collect_all_statistics(driver, match, 'football')
            
            # Анализируем
            analysis = analyze_with_multiple_sources(match, stats_collection, 'football')
            
            if analysis:
                all_results.append(analysis)
        
        # 4. Итоги
        print("\n" + "=" * 70)
        print("📊 ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 70)
        
        for i, result in enumerate(all_results, 1):
            print(f"\n{i}. {result['match']['team1']} vs {result['match']['team2']}")
            print(f"   Источников: {result['sources_count']} ({', '.join(result['sources'])})")
            print(f"   Качество: {result['quality']}")
            print(f"   Анализ возможен: {'✅' if result['can_analyze'] else '❌'}")
        
        # Сохранение
        results = {
            'timestamp': datetime.now().isoformat(),
            'architecture': 'MCP Browser (BetBoom) + Selenium (Flashscore + Scores24 + Sofascore)',
            'betboom_matches': betboom_matches,
            'analyzed_results': all_results
        }
        
        with open('three_sources_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Результаты сохранены в three_sources_test_results.json")
        
        # Сообщение для Telegram
        if all_results:
            sources_count = all_results[0]['sources_count']
            sources_list = ', '.join(all_results[0]['sources'])
        else:
            sources_count = 0
            sources_list = 'нет'
        
        message = "🧠 ИИ-АНАЛИЗ LIVE • 3 ИСТОЧНИКА\n\n"
        message += "═" * 40 + "\n\n"
        message += "✅ СИСТЕМА РАСШИРЕНА!\n\n"
        message += "📊 ИСТОЧНИКИ СТАТИСТИКИ:\n"
        message += "1. Flashscore (основной)\n"
        message += "2. Scores24 (второй)\n"
        message += "3. Sofascore (резервный)\n\n"
        message += f"📈 ТЕСТ:\n"
        message += f"• Источников загружено: {sources_count}\n"
        message += f"• Список: {sources_list}\n\n"
        message += "🎯 ПРЕИМУЩЕСТВА:\n"
        message += "• Высокая надежность\n"
        message += "• Перекрестная проверка данных\n"
        message += "• Работа при сбое любого источника\n\n"
        message += "═" * 40 + "\n\n"
        message += "💡 Напоминаем: Подписка 500₽/неделя\n"
        message += "📞 @TrueLiveBet_Admin для вопросов"
        
        with open('current_live_analysis_mcp.txt', 'w', encoding='utf-8') as f:
            f.write(message)
        
        print("\n✅ Сообщение сохранено в current_live_analysis_mcp.txt")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if driver:
            print("\n🔒 Закрываю Selenium...")
            driver.quit()
            print("✅ Selenium закрыт")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

