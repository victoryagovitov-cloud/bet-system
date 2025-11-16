# -*- coding: utf-8 -*-
"""
ПОЛНЫЙ АНАЛИЗ 22:00 МСК: Футбол + Теннис + Гандбол
"""
import subprocess
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# РЕЗУЛЬТАТЫ ИЗ ПРЕДЫДУЩЕГО АНАЛИЗА + НОВЫЕ

FOOTBALL_MATCHES = [
    {'team1': 'Спортинг', 'team2': 'Брага', 'score': '1-0', 'time': '44\'', 'league': 'Португалия. Примейра Лига', 'odds': '1.27', 'category': 'ХОРОШИЙ'},
    {'team1': 'Модена', 'team2': 'Виртус Энтелла', 'score': '1-0', 'time': '70\'', 'league': 'Италия. Серия B', 'odds': '1.16', 'category': 'ИДЕАЛЬНЫЙ'},
    {'team1': 'Гурник Забже', 'team2': 'Легия Варшава', 'score': '2-0', 'time': '42\'', 'league': 'Польша. Экстракласа', 'odds': '1.16', 'category': 'ХОРОШИЙ'},
]

TENNIS_MATCHES = [
    {'player1': 'Райски М.', 'player2': 'Казума Ли К.', 'score': '1-0 (6:5, 0:0)', 'set': '2-й сет', 'tournament': 'ATP Challenger США', 'odds': '1.12', 'category': 'ИДЕАЛЬНЫЙ', 'note': 'Выиграл 1-й сет 6:5, ведет во 2-м'},
]

HANDBALL_MATCHES = [
    {'team1': 'ИСЕГ', 'team2': 'АСФА Дакар', 'score': '13-9', 'time': 'Перерыв', 'league': 'Сенегал. Чемпионат Элит', 'odds': '1.52', 'category': 'ХОРОШИЙ', 'note': 'Ведет 13:9 после 1-го тайма'},
]

def main():
    from datetime import datetime
    
    now = datetime.now().strftime('%H:%M')
    
    message = f"🧠 ИИ-АНАЛИЗ LIVE • {now} МСК • Честно и просто\n\n"
    message += "═" * 40 + "\n\n"
    
    total = len(FOOTBALL_MATCHES) + len(TENNIS_MATCHES) + len(HANDBALL_MATCHES)
    message += f"✅ НАЙДЕНО: {total} подходящих\n\n"
    
    # ФУТБОЛ
    if FOOTBALL_MATCHES:
        message += "⚽ ФУТБОЛ:\n\n"
        for i, m in enumerate(FOOTBALL_MATCHES, 1):
            message += f"{i}. {m['team1']} – {m['team2']}\n"
            message += f"   {m['league']}\n"
            message += f"   Счет: {m['score']} ({m['time']})\n"
            message += f"   Категория: {m['category']}\n"
            message += f"   Коэфф П1: {m['odds']}\n\n"
    
    # ТЕННИС
    if TENNIS_MATCHES:
        message += "🎾 ТЕННИС:\n\n"
        for i, m in enumerate(TENNIS_MATCHES, len(FOOTBALL_MATCHES)+1):
            message += f"{i}. {m['player1']} vs {m['player2']}\n"
            message += f"   {m['tournament']}\n"
            message += f"   Счет: {m['score']} ({m['set']})\n"
            message += f"   Категория: {m['category']}\n"
            message += f"   Коэфф П1: {m['odds']}\n"
            message += f"   📌 {m['note']}\n\n"
    
    # ГАНДБОЛ
    if HANDBALL_MATCHES:
        message += "🤾 ГАНДБОЛ:\n\n"
        for i, m in enumerate(HANDBALL_MATCHES, len(FOOTBALL_MATCHES)+len(TENNIS_MATCHES)+1):
            message += f"{i}. {m['team1']} – {m['team2']}\n"
            message += f"   {m['league']}\n"
            message += f"   Счет: {m['score']} ({m['time']})\n"
            message += f"   Категория: {m['category']}\n"
            message += f"   Коэфф П1: {m['odds']}\n"
            message += f"   📌 {m['note']}\n\n"
    
    message += "💡 Категории:\n"
    message += "• МЕРТВЫЙ: 80+ мин, коэфф <1.15\n"
    message += "• ИДЕАЛЬНЫЙ: 60+ мин, коэфф <1.30\n"
    message += "• ОТЛИЧНЫЙ: 45+ мин, коэфф <1.50\n"
    message += "• ХОРОШИЙ: остальные подходящие\n\n"
    message += "═" * 40 + "\n\n"
    message += "💡 Напоминаем: Подписка 500₽/неделя\n"
    message += "📞 @TrueLiveBet_Admin для вопросов\n"
    message += "💬 Обратная связь: пишите личные сообщения"
    
    # Сохраняем
    with open('current_live_analysis_mcp.txt', 'w', encoding='utf-8') as f:
        f.write(message)
    
    print("=" * 60)
    print("✅ ПОЛНЫЙ АНАЛИЗ 22:00 МСК ГОТОВ")
    print("=" * 60)
    print(f"\n⚽ Футбол: {len(FOOTBALL_MATCHES)}")
    print(f"🎾 Теннис: {len(TENNIS_MATCHES)}")
    print(f"🤾 Гандбол: {len(HANDBALL_MATCHES)}")
    print(f"\n📊 ВСЕГО: {total} подходящих матчей\n")
    
    # Отправляем
    print("📤 Отправка в @TrueLiveBet...")
    result = subprocess.run(['python', 'send_fixed_analysis.py'], 
                          capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode == 0:
        print("✅ Отправлено успешно!")
        print("\n" + message)
    else:
        print(f"❌ Ошибка отправки: {result.stderr}")

if __name__ == "__main__":
    main()

