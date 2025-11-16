# -*- coding: utf-8 -*-
"""
✅ ПОЛНАЯ СИСТЕМА С MCP + ПРЕФИЛЬТР + SCORES24

АЛГОРИТМ:
1. MCP → BetBoom → получить все live-матчи
2. ПРЕФИЛЬТР (УМНЫЙ):
   Футбол: неничейный + фаворит ведет + коэфф ≤2.5
   Теннис: (выиграл 1-й сет + ведет во 2-м) ИЛИ (ведет 3+ гейма в 1-м) + коэфф ≤2.5
   Гандбол: неничейный + фаворит ведет + коэфф ≤2.5
3. Scores24 → проверить ТОЛЬКО отфильтрованные
4. Telegram → отправить
"""
from improved_scores24_connector import setup_driver_improved, check_scores24_improved
import requests
import urllib3
import json
from datetime import datetime
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

BOT_TOKEN = CONFIG['notifications']['telegram']['bot_token']
CHANNEL = CONFIG['notifications']['telegram']['channel_username']

# ===================== УТИЛИТЫ =====================

def parse_score(score_str):
    """Парсит счет типа '2:0' или '1:1'"""
    try:
        if ':' not in score_str:
            return None, None
        
        parts = score_str.split(':')
        score1 = int(parts[0].strip())
        score2 = int(parts[1].split()[0].strip())
        return score1, score2
    except:
        return None, None

def parse_tennis_score(score_str):
    """
    Парсит теннисный счет типа:
    '6:4, 3:1' → сеты: [(6,4)], текущий: (3,1)
    '6:2, 5:4' → сеты: [(6,2)], текущий: (5,4)
    """
    try:
        parts = score_str.split(',')
        sets = []
        current_set = None
        
        for part in parts:
            if ':' in part:
                s1, s2 = parse_score(part.strip())
                if s1 is not None:
                    # Завершенный сет: разница >= 2 или один = 7
                    if abs(s1 - s2) >= 2 or s1 == 7 or s2 == 7:
                        sets.append((s1, s2))
                    else:
                        current_set = (s1, s2)
        
        return sets, current_set
    except:
        return [], None

# ===================== ФУТБОЛ - ПРЕФИЛЬТР =====================

def is_draw_football(score_str):
    """Проверяет ничью"""
    score1, score2 = parse_score(score_str)
    if score1 is None:
        return True
    return score1 == score2

def is_favorite_leading_football(score_str, odds):
    """Фаворит (коэфф < 2.5) ведет"""
    score1, score2 = parse_score(score_str)
    if score1 is None or odds > 2.5:
        return False
    return score1 > score2

def prefilter_football(match):
    """
    ФУТБОЛ - КРИТЕРИИ:
    ✅ Неничейный счет
    ✅ Коэффициент ≤ 2.5
    ✅ Фаворит ведет (score1 > score2)
    """
    score = match.get('score', '')
    odds = match.get('odds', 999)
    
    if is_draw_football(score):
        return False, "НИЧЬЯ"
    
    if odds > 2.5:
        return False, f"АУТСАЙДЕР (коэфф {odds})"
    
    if not is_favorite_leading_football(score, odds):
        return False, "Фаворит не ведет"
    
    return True, "ОК"

# ===================== ТЕННИС - ПРЕФИЛЬТР =====================

def prefilter_tennis(match):
    """
    ТЕННИС - КРИТЕРИИ:
    ✅ Коэффициент ≤ 2.5
    ✅ (Выиграл 1-й сет + ведет во 2-м) ИЛИ (ведет в 1-м сете 3+ гейма)
    """
    score = match.get('score', '')
    odds = match.get('odds', 999)
    
    if odds > 2.5:
        return False, f"АУТСАЙДЕР (коэфф {odds})"
    
    sets, current_set = parse_tennis_score(score)
    
    # ВАРИАНТ 1: Выиграл 1-й сет + ведет во 2-м
    if len(sets) >= 1:
        # Проверяем что выиграл первый сет
        if sets[0][0] > sets[0][1]:
            # Если есть текущий сет - проверяем что ведет
            if current_set:
                if current_set[0] > current_set[1]:
                    return True, "Выиграл 1-й сет + ведет во 2-м"
            else:
                # 2-й сет еще не начался
                return True, "Выиграл 1-й сет (2-й не начался)"
    
    # ВАРИАНТ 2: Ведет в 1-м сете с отрывом 3+ гейма
    if current_set and len(sets) == 0:
        games1, games2 = current_set
        if games1 - games2 >= 3:
            return True, f"Ведет {games1}:{games2} в 1-м сете"
    
    return False, "Не подходит по счету"

# ===================== ГАНДБОЛ - ПРЕФИЛЬТР =====================

def prefilter_handball(match):
    """
    ГАНДБОЛ - КРИТЕРИИ:
    ✅ Неничейный счет
    ✅ Коэффициент ≤ 2.5
    ✅ Фаворит ведет
    """
    score = match.get('score', '')
    odds = match.get('odds', 999)
    
    score1, score2 = parse_score(score)
    
    if score1 is None:
        return False, "Не удалось распарсить счет"
    
    if score1 == score2:
        return False, "НИЧЬЯ"
    
    if odds > 2.5:
        return False, f"АУТСАЙДЕР (коэфф {odds})"
    
    if score1 <= score2:
        return False, "Фаворит не ведет"
    
    return True, "ОК"

# ===================== ОБЩАЯ ФИЛЬТРАЦИЯ =====================

def prefilter_all_matches(all_matches):
    """
    Применяет префильтр ко ВСЕМ видам спорта
    """
    print("\n" + "="*70)
    print("🔍 ШАГ 1: ПРЕФИЛЬТРАЦИЯ НА BETBOOM")
    print("="*70 + "\n")
    
    filtered = {'football': [], 'tennis': [], 'handball': []}
    stats = {
        'total': 0,
        'passed': 0,
        'filtered_by_sport': {'football': 0, 'tennis': 0, 'handball': 0},
        'reasons': {}
    }
    
    sport_filters = {
        'football': prefilter_football,
        'tennis': prefilter_tennis,
        'handball': prefilter_handball
    }
    
    sport_icons = {
        'football': '⚽',
        'tennis': '🎾',
        'handball': '🤾'
    }
    
    for sport in ['football', 'tennis', 'handball']:
        if not all_matches.get(sport):
            continue
        
        icon = sport_icons[sport]
        print(f"{icon} {sport.upper()}: {len(all_matches[sport])} матчей\n")
        
        for match in all_matches[sport]:
            stats['total'] += 1
            
            team1 = match.get('team1') or match.get('player1')
            team2 = match.get('team2') or match.get('player2')
            score = match.get('score', '')
            odds = match.get('odds', 999)
            
            print(f"   {team1} - {team2}")
            print(f"   Счет: {score}, Коэфф: {odds}")
            
            # Применяем фильтр
            passed, reason = sport_filters[sport](match)
            
            if passed:
                print(f"   ✅ ПОДХОДИТ - {reason}\n")
                stats['passed'] += 1
                filtered[sport].append(match)
            else:
                print(f"   ❌ {reason}\n")
                stats['filtered_by_sport'][sport] += 1
                stats['reasons'][reason] = stats['reasons'].get(reason, 0) + 1
    
    # Итоги
    print("="*70)
    print("📊 ИТОГИ ПРЕФИЛЬТРАЦИИ")
    print("="*70)
    print(f"Всего матчей: {stats['total']}")
    print(f"Прошли фильтр: {stats['passed']}")
    print(f"\nОтфильтровано по видам спорта:")
    for sport, count in stats['filtered_by_sport'].items():
        if count > 0:
            print(f"  {sport_icons[sport]} {sport}: {count}")
    print(f"\nПричины фильтрации:")
    for reason, count in sorted(stats['reasons'].items(), key=lambda x: -x[1]):
        print(f"  • {reason}: {count}")
    print("="*70 + "\n")
    
    return filtered, stats

# ===================== ПРОВЕРКА НА SCORES24 =====================

def verify_on_scores24(filtered_matches):
    """Проверка ТОЛЬКО отфильтрованных матчей"""
    print("="*70)
    print("🔍 ШАГ 2: ПРОВЕРКА НА SCORES24")
    print("="*70 + "\n")
    
    if not any(filtered_matches.values()):
        print("⚠️ Нет матчей для проверки\n")
        return []
    
    driver = setup_driver_improved()
    verified = []
    
    try:
        for sport in ['football', 'tennis', 'handball']:
            if not filtered_matches[sport]:
                continue
            
            sport_icon = {'football': '⚽', 'tennis': '🎾', 'handball': '🤾'}[sport]
            print(f"{sport_icon} {sport.upper()}: {len(filtered_matches[sport])} матчей\n")
            
            for i, match in enumerate(filtered_matches[sport], 1):
                team1 = match.get('team1') or match.get('player1')
                team2 = match.get('team2') or match.get('player2')
                
                print(f"[{i}/{len(filtered_matches[sport])}]")
                
                result = check_scores24_improved(
                    driver, sport,
                    team1, team2,
                    match
                )
                
                if result['verified']:
                    verified.append((sport, result))
                    print(f"✅ ПОДТВЕРЖДЕН\n")
                else:
                    print(f"❌ Не найден\n")
    
    finally:
        driver.quit()
        print("🔧 Драйвер закрыт\n")
    
    return verified

# ===================== ОТПРАВКА В TELEGRAM =====================

def send_results(verified_matches, filter_stats):
    """Отправка результатов"""
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
Не проверяем ничьи и аутсайдеров на Scores24

---
⏰ Время анализа: {current_time} МСК
📈 Следующая проверка через 45 минут

🤖 TrueLiveBet | Честные прогнозы live-ставок
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
        
        # Футбол
        if by_sport['football']:
            message += "⚽ ФУТБОЛ:\n\n"
            for i, data in enumerate(by_sport['football'], 1):
                m = data['match']
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
                message += f"{i}️⃣ {p1} - {p2}\n"
                message += f"   {m.get('tournament') or m.get('league')}\n"
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

---
⏰ {current_time} МСК
📈 УМНЫЙ АНАЛИЗ С ПРЕФИЛЬТРОМ
✅ БЕЗ ЛИШНИХ ПРОВЕРОК!

🤖 TrueLiveBet | Честные прогнозы live-ставок
───────────────────────────────────"""
    
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {'chat_id': CHANNEL, 'text': message}
    
    try:
        response = requests.post(url, json=payload, timeout=10, verify=False)
        response.raise_for_status()
        print(f"✅ Отправлено в {CHANNEL}\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}\n")
        return False

# ===================== MCP → BETBOOM =====================

def get_betboom_matches_mcp():
    """
    Получение матчей с BetBoom через MCP
    TODO: интеграция с реальным MCP
    """
    print("="*70)
    print("📡 ПОЛУЧЕНИЕ ДАННЫХ С BETBOOM (MCP)")
    print("="*70 + "\n")
    
    # Здесь будет реальный MCP запрос
    # Пока используем тестовые данные
    
    print("⚠️ ТЕСТОВЫЙ РЕЖИМ - используются заранее заданные матчи\n")
    
    return {
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
            }
        ],
        'tennis': [
            {
                'player1': 'Синнер Я.',
                'player2': 'Медведев Д.',
                'tournament': 'ATP Shanghai',
                'score': '6:4, 3:1',
                'odds': 1.15
            },
            {
                'player1': 'Иванов И.',
                'player2': 'Петров П.',
                'tournament': 'Challenger Minsk',
                'score': '5:3',
                'odds': 1.80
            }
        ],
        'handball': [
            {
                'team1': 'ПСЖ',
                'team2': 'Барселона',
                'league': 'Лига Чемпионов',
                'score': '18:18',
                'time': '2Т, 45 мин',
                'odds': 2.10
            }
        ]
    }

# ===================== ГЛАВНАЯ ФУНКЦИЯ =====================

def main():
    """
    ПОЛНЫЙ ЦИКЛ:
    MCP → Префильтр → Scores24 → Telegram
    """
    print("\n" + "="*70)
    print("🚀 ПОЛНЫЙ АНАЛИЗ С УМНЫМ ПРЕФИЛЬТРОМ")
    print("="*70 + "\n")
    
    # ШАГ 0: Получение данных с BetBoom
    all_matches = get_betboom_matches_mcp()
    
    # ШАГ 1: Префильтрация
    filtered, filter_stats = prefilter_all_matches(all_matches)
    
    # ШАГ 2: Проверка на Scores24
    verified = verify_on_scores24(filtered)
    
    # ШАГ 3: Отправка в Telegram
    print("="*70)
    print("📤 ШАГ 3: ОТПРАВКА В TELEGRAM")
    print("="*70 + "\n")
    send_results(verified, filter_stats)
    
    print("\n" + "="*70)
    print("✅ АНАЛИЗ ЗАВЕРШЕН!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()

