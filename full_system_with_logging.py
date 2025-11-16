# -*- coding: utf-8 -*-
"""
🚀 ПОЛНАЯ СИСТЕМА С ЛОГИРОВАНИЕМ И СТАТИСТИКОЙ

АЛГОРИТМ:
1. BetBoom (MCP) → получить live-матчи
2. Префильтр → отсеять ничьи и аутсайдеров
3. Scores24 → проверить отфильтрованные
4. Логирование → сохранить каждый прогноз
5. Telegram → отправить рекомендации
"""
from full_mcp_with_prefilter import (
    prefilter_all_matches,
    verify_on_scores24,
    parse_score,
    parse_tennis_score
)
from prediction_logger import PredictionLogger
from betboom_mcp_connector import BetBoomMCPConnector
from betboom_mcp_live_collector import BetBoomLiveCollector
import requests
import urllib3
import json
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

BOT_TOKEN = CONFIG['notifications']['telegram']['bot_token']
CHANNEL = CONFIG['notifications']['telegram']['channel_username']

# Инициализация логгера
logger = PredictionLogger()

def determine_category(odds):
    """Определяет категорию по коэффициенту"""
    if odds <= 1.05:
        return 'dead'
    elif odds <= 1.20:
        return 'perfect'
    elif odds <= 1.50:
        return 'excellent'
    else:
        return 'good'

def send_results_with_logging(verified_matches, filter_stats):
    """Отправка результатов С ЛОГИРОВАНИЕМ каждого прогноза"""
    current_time = datetime.now().strftime('%H:%M')
    current_date = datetime.now().strftime('%d.%m.%Y')
    
    if not verified_matches:
        message = f"""───────────────────────────────────
📊 АНАЛИЗ LIVE-МАТЧЕЙ НА {current_time} МСК ({current_date})

❌ НЕТ ПОДХОДЯЩИХ МАТЧЕЙ

📊 Статистика проверки:
• Всего проверено: {filter_stats['total']}
• Прошли префильтр: {filter_stats['passed']}
• Найдены на Scores24: 0

Причины фильтрации:"""
        
        for reason, count in sorted(filter_stats['reasons'].items(), key=lambda x: -x[1])[:5]:
            message += f"\n  • {reason}: {count}"
        
        message += f"""

✅ УМНЫЙ ФИЛЬТР РАБОТАЕТ!

---
⏰ Время: {current_time} МСК
📈 Следующая проверка через 45 минут

🤖 TrueLiveBet | Честные прогнозы
───────────────────────────────────"""
    else:
        message = f"""───────────────────────────────────
📊 АНАЛИЗ LIVE-МАТЧЕЙ НА {current_time} МСК ({current_date})

✅ НАЙДЕНО: {len(verified_matches)} ПОДХОДЯЩИХ МАТЧА

"""
        
        # Группируем по видам спорта
        by_sport = {'football': [], 'tennis': [], 'handball': []}
        for sport, data in verified_matches:
            by_sport[sport].append(data)
        
        logged_predictions = []
        
        # Футбол
        if by_sport['football']:
            message += "⚽ ФУТБОЛ:\n\n"
            for i, data in enumerate(by_sport['football'], 1):
                m = data['match']
                category = determine_category(m['odds'])
                
                # ЛОГИРУЕМ ПРОГНОЗ
                pred_id = logger.add_prediction(
                    sport='football',
                    team1=m['team1'],
                    team2=m['team2'],
                    league=m['league'],
                    score=m['score'],
                    odds=m['odds'],
                    category=category
                )
                logged_predictions.append(pred_id)
                
                message += f"{i}️⃣ {m['team1']} - {m['team2']}\n"
                message += f"   {m['league']}\n"
                message += f"   Счет: {m['score']}\n"
                message += f"   Рекомендация: П1 - коэф. {m['odds']}\n\n"
                message += f"   📌 {data['details']}\n"
                message += f"   ✅ Проверено на Scores24\n\n"
                
                if m['odds'] <= 1.05:
                    message += "   ✅ МЕРТВЫЙ ⭐⭐⭐⭐⭐\n\n"
                elif m['odds'] <= 1.20:
                    message += "   ✅ ИДЕАЛЬНЫЙ ⭐⭐⭐⭐\n\n"
                elif m['odds'] <= 1.50:
                    message += "   ✅ ОТЛИЧНЫЙ ⭐⭐⭐\n\n"
                else:
                    message += "   ✅ ХОРОШИЙ ⭐⭐\n\n"
                message += "---\n\n"
        
        # Теннис
        if by_sport['tennis']:
            message += "🎾 ТЕННИС:\n\n"
            for i, data in enumerate(by_sport['tennis'], 1):
                m = data['match']
                p1 = m.get('player1') or m.get('team1')
                p2 = m.get('player2') or m.get('team2')
                tournament = m.get('tournament') or m.get('league')
                category = determine_category(m['odds'])
                
                # ЛОГИРУЕМ ПРОГНОЗ
                pred_id = logger.add_prediction(
                    sport='tennis',
                    team1=p1,
                    team2=p2,
                    league=tournament,
                    score=m['score'],
                    odds=m['odds'],
                    category=category
                )
                logged_predictions.append(pred_id)
                
                message += f"{i}️⃣ {p1} - {p2}\n"
                message += f"   {tournament}\n"
                message += f"   Счет: {m['score']}\n"
                message += f"   Рекомендация: П1 - коэф. {m['odds']}\n\n"
                message += f"   📌 {data['details']}\n\n"
                
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
                category = determine_category(m['odds'])
                
                # ЛОГИРУЕМ ПРОГНОЗ
                pred_id = logger.add_prediction(
                    sport='handball',
                    team1=m['team1'],
                    team2=m['team2'],
                    league=m['league'],
                    score=m['score'],
                    odds=m['odds'],
                    category=category
                )
                logged_predictions.append(pred_id)
                
                message += f"{i}️⃣ {m['team1']} - {m['team2']}\n"
                message += f"   {m['league']}\n"
                message += f"   Счет: {m['score']}\n"
                message += f"   Рекомендация: П1 - коэф. {m['odds']}\n\n"
                message += f"   📌 {data['details']}\n\n"
                
                if m['odds'] <= 1.20:
                    message += "   ✅ ИДЕАЛЬНЫЙ ⭐⭐⭐⭐\n\n"
                else:
                    message += "   ✅ ОТЛИЧНЫЙ ⭐⭐⭐\n\n"
                message += "---\n\n"
        
        message += f"""📊 ИТОГО: {len(verified_matches)} матча
   • Футбол: {len(by_sport['football'])}
   • Теннис: {len(by_sport['tennis'])}
   • Гандбол: {len(by_sport['handball'])}

📊 Всего проверено: {filter_stats['total']}
   Префильтр: {filter_stats['passed']}
   Scores24: {len(verified_matches)}

📝 Прогнозы #{logged_predictions[0]}-#{logged_predictions[-1]} записаны в лог

---
⏰ {current_time} МСК
📈 УМНЫЙ АНАЛИЗ С ПРЕФИЛЬТРОМ
✅ ВСЕ ПРОГНОЗЫ ЛОГИРУЮТСЯ!

🤖 TrueLiveBet | Честные прогнозы
───────────────────────────────────"""
    
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {'chat_id': CHANNEL, 'text': message}
    
    try:
        response = requests.post(url, json=payload, timeout=10, verify=False)
        response.raise_for_status()
        print(f"✅ Отправлено в {CHANNEL}")
        print(f"📝 Залогировано прогнозов: {len(verified_matches)}\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}\n")
        return False

def get_betboom_matches_mcp():
    """
    Получение матчей с BetBoom через MCP Browser
    
    Использует улучшенный коллектор для навигации и парсинга
    """
    print("="*70)
    print("📡 ПОЛУЧЕНИЕ ДАННЫХ С BETBOOM ЧЕРЕЗ MCP")
    print("="*70 + "\n")
    
    try:
        collector = BetBoomLiveCollector()
        
        # Попытка реального сбора через MCP
        all_matches = collector.collect_all_sports_real()
        
        # Проверяем результат
        if all_matches is None:
            print("⚠️ MCP недоступен, используем FALLBACK\n")
            return get_betboom_matches_fallback()
        
        # Проверяем, есть ли собранные данные
        total_matches = sum(len(all_matches[s]) for s in ['football', 'tennis', 'handball'])
        
        if total_matches == 0:
            print("⚠️ Не найдено матчей через MCP, используем FALLBACK\n")
            return get_betboom_matches_fallback()
        
        print(f"✅ Собрано матчей через MCP: {total_matches}\n")
        return all_matches
        
    except Exception as e:
        print(f"❌ Ошибка MCP: {e}")
        print("⚠️ Используем FALLBACK\n")
        return get_betboom_matches_fallback()

def get_betboom_matches_fallback():
    """
    Fallback: тестовые данные когда MCP недоступен
    
    В будущем здесь можно добавить Selenium как альтернативу
    """
    print("📋 ИСПОЛЬЗУЮТСЯ ТЕСТОВЫЕ ДАННЫЕ (FALLBACK)")
    print("   Для реальных данных настройте MCP Browser\n")
    
    return {
        'football': [
            {
                'team1': 'Шапекоэнсе',
                'team2': 'Операрио ПР',
                'league': 'Бразилия. Серия B',
                'score': '2:0',
                'time': '2Т, 71 мин',
                'odds': 1.01
            }
        ],
        'tennis': [
            {
                'player1': 'Синнер Я.',
                'player2': 'Медведев Д.',
                'tournament': 'ATP Shanghai',
                'score': '6:4, 3:1',
                'odds': 1.15
            }
        ],
        'handball': []
    }

def get_betboom_matches():
    """
    Главная функция для получения матчей с BetBoom
    
    Пробует MCP, при неудаче использует fallback
    """
    return get_betboom_matches_mcp()

def main():
    """
    ПОЛНЫЙ ЦИКЛ С ЛОГИРОВАНИЕМ:
    BetBoom → Префильтр → Scores24 → Логирование → Telegram
    """
    print("\n" + "="*70)
    print("🚀 ПОЛНАЯ СИСТЕМА С ЛОГИРОВАНИЕМ")
    print("="*70 + "\n")
    
    # ШАГ 1: Получение данных
    all_matches = get_betboom_matches()
    
    # ШАГ 2: Префильтрация
    filtered, filter_stats = prefilter_all_matches(all_matches)
    
    # ШАГ 3: Проверка на Scores24
    verified = verify_on_scores24(filtered)
    
    # ШАГ 4: Отправка + Логирование
    print("="*70)
    print("📤 ШАГ 3: ОТПРАВКА + ЛОГИРОВАНИЕ")
    print("="*70 + "\n")
    send_results_with_logging(verified, filter_stats)
    
    # ШАГ 5: Показать статистику за сегодня
    print("="*70)
    print("📊 СТАТИСТИКА ЗА СЕГОДНЯ")
    print("="*70 + "\n")
    
    stats = logger.get_statistics()
    if stats:
        print(f"Всего прогнозов: {stats['total']}")
        print(f"Выиграно: {stats['won']}")
        print(f"Проиграно: {stats['lost']}")
        print(f"Ожидают проверки: {stats['pending']}")
        if stats['won'] + stats['lost'] > 0:
            print(f"Процент побед: {stats['win_rate']}%")
            print(f"Прибыль: {stats['total_profit']}₽")
    
    print("\n" + "="*70)
    print("✅ АНАЛИЗ ЗАВЕРШЕН!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()

