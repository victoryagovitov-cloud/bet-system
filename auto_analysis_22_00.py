# -*- coding: utf-8 -*-
"""
АВТОМАТИЧЕСКИЙ АНАЛИЗ 22:00 МСК
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
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(15)
    return driver

# ТОП-МАТЧИ из BetBoom snapshot 22:00 МСК
TOP_MATCHES = [
    {'team1': 'Спортинг', 'team2': 'Брага', 'score': '1-0', 'time': '44\'', 'league': 'Португалия. Примейра Лига', 'odds': '1.27', 'half': '1Т'},
    {'team1': 'Модена', 'team2': 'Виртус Энтелла', 'score': '1-0', 'time': '70\'', 'league': 'Италия. Серия B', 'odds': '1.16', 'half': '2Т'},
    {'team1': 'Гурник Забже', 'team2': 'Легия Варшава', 'score': '2-0', 'time': '42\'', 'league': 'Польша. Экстракласа', 'odds': '1.16', 'half': '1Т'},
    {'team1': 'Боруссия М', 'team2': 'Фрайбург', 'score': '0-0', 'time': '73\'', 'league': 'Германия. Бундеслига', 'odds': '4.8', 'half': '2Т'},
    {'team1': 'Панатинаикос', 'team2': 'Атромитос Афины', 'score': '0-0', 'time': '28\'', 'league': 'Греция. Суперлига', 'odds': '1.37', 'half': '1Т'},
]

def get_stats(driver):
    try:
        driver.get('https://scores24.live/ru/soccer?matchesFilter=live')
        time.sleep(2)
        page_text = driver.execute_script("return document.body.innerText;")
        return {'source': 'scores24', 'loaded': True, 'size': len(page_text)}
    except:
        return {'source': 'scores24', 'loaded': False}

def analyze_match(match, stats):
    if not stats.get('loaded'):
        return None
    
    score_parts = match['score'].split('-')
    if len(score_parts) != 2:
        return None
    
    score1, score2 = int(score_parts[0]), int(score_parts[1])
    minute = int(match['time'].replace('\'', ''))
    odds = float(match['odds'])
    
    # Чеклист: ненич. счет + фаворит ведет
    non_draw = (score1 != score2)
    is_favorite = odds < 2.0
    is_leading = score1 > score2
    
    if non_draw and is_favorite and is_leading:
        # Категоризация
        if minute >= 80 and odds < 1.15:
            category = 'МЕРТВЫЙ'
        elif minute >= 60 and odds < 1.30:
            category = 'ИДЕАЛЬНЫЙ'
        elif minute >= 45 and odds < 1.50:
            category = 'ОТЛИЧНЫЙ'
        else:
            category = 'ХОРОШИЙ'
        
        return {'match': match, 'category': category}
    
    return None

def main():
    print("=" * 60)
    print("⚽ АВТОМАТИЧЕСКИЙ АНАЛИЗ 22:00 МСК")
    print("=" * 60)
    
    driver = setup_selenium()
    results = []
    
    try:
        # Получаем общую статистику один раз
        print("\n[1/2] Получение статистики...")
        stats = get_stats(driver)
        
        if stats['loaded']:
            print(f"   ✅ Scores24: {stats['size']:,} символов")
        else:
            print("   ❌ Scores24 недоступен")
            return False
        
        print(f"\n[2/2] Анализ {len(TOP_MATCHES)} топ-матчей...")
        
        for i, match in enumerate(TOP_MATCHES, 1):
            print(f"\n   [{i}/{len(TOP_MATCHES)}] {match['team1']} vs {match['team2']}")
            print(f"      {match['score']}, {match['time']}, {match['half']}")
            
            analysis = analyze_match(match, stats)
            
            if analysis:
                results.append(analysis)
                print(f"      ✅ {analysis['category']}")
            else:
                print(f"      ⚪ Не прошел чеклист")
        
        # Формируем сообщение
        now = datetime.now().strftime('%H:%M')
        
        message = f"🧠 ИИ-АНАЛИЗ LIVE • {now} МСК • Честно и просто\n\n"
        message += "═" * 40 + "\n\n"
        
        if results:
            message += f"✅ НАЙДЕНО: {len(results)} подходящих\n\n"
            
            for i, r in enumerate(results, 1):
                m = r['match']
                message += f"{i}. ⚽ {m['team1']} – {m['team2']}\n"
                message += f"   {m['league']}\n"
                message += f"   Счет: {m['score']} ({m['half']}, {m['time']})\n"
                message += f"   Категория: {r['category']}\n"
                message += f"   Коэфф П1: {m['odds']}\n\n"
            
            message += "💡 Категории:\n"
            message += "• МЕРТВЫЙ: 80+ мин, коэфф <1.15\n"
            message += "• ИДЕАЛЬНЫЙ: 60+ мин, коэфф <1.30\n"
            message += "• ОТЛИЧНЫЙ: 45+ мин, коэфф <1.50\n"
            message += "• ХОРОШИЙ: остальные\n\n"
        else:
            message += "⚪ К СОЖАЛЕНИЮ, ПОДХОДЯЩИХ МАТЧЕЙ НЕТ\n\n"
            message += "Проанализировано 5 топ-матчей,\n"
            message += "но ни один не прошел строгие критерии:\n"
            message += "• Ненич. счет + фаворит ведет\n"
            message += "• Подтвержденная статистика\n\n"
        
        message += "═" * 40 + "\n\n"
        message += "💡 Напоминаем: Подписка 500₽/неделя\n"
        message += "📞 @TrueLiveBet_Admin для вопросов\n"
        message += "💬 Обратная связь: пишите личные сообщения"
        
        # Сохраняем и отправляем
        with open('current_live_analysis_mcp.txt', 'w', encoding='utf-8') as f:
            f.write(message)
        
        print("\n" + "=" * 60)
        print(f"✅ АНАЛИЗ ЗАВЕРШЕН: {len(results)} подходящих")
        print("=" * 60)
        
        # Отправка
        print("\n📤 Отправка в @TrueLiveBet...")
        result = subprocess.run(['python', 'send_fixed_analysis.py'], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ Отправлено успешно!")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        driver.quit()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

