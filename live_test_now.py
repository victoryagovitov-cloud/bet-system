# -*- coding: utf-8 -*-
"""
🔥 ТЕСТ НА РЕАЛЬНЫХ LIVE-МАТЧАХ ПРЯМО СЕЙЧАС
"""
# Импортируем наш умный анализатор
from smart_live_analyzer import setup_driver, check_on_scores24, format_and_send
import time

print("\n" + "="*70)
print("🔥 ТЕСТ НА РЕАЛЬНЫХ LIVE-МАТЧАХ (02:40 МСК)")
print("="*70 + "\n")

# Актуальные матчи с BetBoom (только что получили через MCP)
current_matches = {
    'football': [
        {
            'team1': 'Шапекоэнсе',
            'team2': 'Операрио ПР',
            'league': 'Бразилия. Серия B',
            'score': '2:0',
            'time': '2Т, 71 мин',
            'odds': 1.01
        },
        {
            'team1': 'ФК Цинциннати',
            'team2': 'Коламбус Крю',
            'league': 'США. MLS',
            'score': '0:0',
            'time': '1Т, 35 мин',
            'odds': 2.6
        },
        {
            'team1': 'Насиональ А',
            'team2': 'Серро Портеньо',
            'league': 'Парагвай. Примера Дивизион',
            'score': '1:1',
            'time': '1Т, 31 мин',
            'odds': 6.75
        }
    ],
    'tennis': [],
    'handball': []
}

start_time = time.time()

# Запускаем проверку
driver = setup_driver()
verified = []

try:
    print("⚽ ФУТБОЛ (3 матча):\n")
    
    for i, match in enumerate(current_matches['football'], 1):
        print(f"[{i}/3] {match['team1']} - {match['team2']} ({match['score']})")
        
        result = check_on_scores24(
            driver, 'football',
            match['team1'], match['team2'],
            match
        )
        
        if result['verified']:
            verified.append(('football', result))
            print(f"      ✅ ПОДТВЕРЖДЕНО!\n")
        else:
            print(f"      ❌ Не подтверждено\n")
finally:
    driver.quit()
    print("🔧 Драйвер закрыт\n")

# Итоги
print("="*70)
print("📊 ИТОГИ РЕАЛЬНОГО ТЕСТА")
print("="*70)
print(f"Проверено: 3 матча")
print(f"Подтверждено на Scores24: {len(verified)}")
print(f"Время: {time.time() - start_time:.1f}с")
print("="*70 + "\n")

# Отправляем
if verified:
    print("📤 Отправляю ПРОВЕРЕННЫЕ матчи в Telegram...\n")
    format_and_send(verified)
else:
    print("⚠️ Нет проверенных матчей для отправки\n")

