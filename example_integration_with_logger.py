# -*- coding: utf-8 -*-
"""
ПРИМЕР ИНТЕГРАЦИИ ЛОГГЕРА ПРОГНОЗОВ В ОСНОВНОЙ WORKFLOW

Этот файл показывает, как интегрировать логирование прогнозов
в существующую систему анализа
"""
from datetime import datetime
from prediction_logger import PredictionLogger

def example_analysis_with_logging():
    """
    Пример функции анализа матчей с логированием
    """
    
    # Инициализируем логгер
    logger = PredictionLogger()
    
    # Имитация результатов анализа (в реальной системе это будет из BetBoom/Scores24)
    suitable_matches = [
        {
            'sport': 'Футбол',
            'tournament': 'Экстракласа Польша',
            'team1': 'Ягеллония',
            'team2': 'Корона Кельце',
            'score': '2:0',
            'minute': '57\'',
            'recommendation': 'П1',
            'odds': 2.02,
            'category': 'ОТЛИЧНЫЙ ⭐⭐⭐',
            'analysis': 'Фаворит ведет 2:0 в 57-й минуте. Уверенный контроль игры.',
            'url': 'https://scores24.live/ru/soccer/m-06-10-2025-jagiellonia-korona-kielce',
            'team1_position': '5',
            'team2_position': '2',
            'sources_checked': ['Scores24', 'Flashscore']
        },
        {
            'sport': 'Теннис',
            'tournament': 'WTA 125 Мальорка',
            'team1': 'Теодора Костович',
            'team2': 'Екатерина Казионова',
            'score': '1:0 (6:2, 5:0)',
            'minute': '2-й сет',
            'recommendation': 'П1',
            'odds': 1.01,
            'category': 'ИДЕАЛЬНЫЙ ⭐⭐⭐⭐',
            'analysis': 'Выиграла 1-й сет 6:2, ведет во 2-м 5:0. Рейтинг WTA 225 vs 369.',
            'url': 'https://scores24.live/ru/tennis/m-05-10-2025-teodora-kostovic-ekaterina-kazionova',
            'team1_position': 'WTA 225',
            'team2_position': 'WTA 369',
            'sources_checked': ['Scores24', 'WTA Rankings']
        }
    ]
    
    # Обрабатываем каждый матч
    logged_matches = []
    
    for match in suitable_matches:
        # 1. ФОРМИРУЕМ СООБЩЕНИЕ ДЛЯ TELEGRAM
        telegram_message = f"""
{match['team1']} - {match['team2']}
{match['tournament']}

Счет: {match['score']} ({match['minute']})

Рекомендация: {match['recommendation']} - коэф. {match['odds']}

📌 Анализ:
{match['analysis']}

Источники: {', '.join(match['sources_checked'])}

✅ Категория: {match['category']}
"""
        
        # 2. ОТПРАВЛЯЕМ В TELEGRAM (здесь ваш код отправки)
        print(f"\n📤 ОТПРАВКА В TELEGRAM:")
        print(telegram_message)
        
        # 3. ЛОГИРУЕМ ПРОГНОЗ
        prediction_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'sport': match['sport'],
            'tournament': match['tournament'],
            'team1': match['team1'],
            'team2': match['team2'],
            'score_at_prediction': match['score'],
            'minute_at_prediction': match['minute'],
            'recommendation': match['recommendation'],
            'odds': match['odds'],
            'category': match['category'],
            'reason': match['analysis'],
            'match_url': match['url'],
            'league_position_team1': match['team1_position'],
            'league_position_team2': match['team2_position'],
            'stats_checked': match['sources_checked'],
        }
        
        match_id = logger.log_prediction(prediction_data)
        print(f"✅ Прогноз залогирован: {match_id}")
        
        logged_matches.append(match_id)
    
    print(f"\n📊 Всего залогировано прогнозов: {len(logged_matches)}")
    return logged_matches


def example_update_results():
    """
    Пример обновления результатов вечером (после окончания матчей)
    """
    from prediction_checker import PredictionChecker
    
    checker = PredictionChecker()
    
    # Примеры обновления результатов
    results = [
        {
            'match_id': 'ягеллония-vs-корона-кельце-2025-10-06',
            'final_score': '3:0'
        },
        {
            'match_id': 'теодора-костович-vs-екатерина-казионова-2025-10-06',
            'final_score': '2:0'  # В теннисе это сеты
        }
    ]
    
    for result in results:
        is_correct = checker.check_prediction_result(
            result['match_id'],
            result['final_score']
        )
        print(f"✅ {result['match_id']}: {'Правильно' if is_correct else 'Неправильно'}")


def example_generate_and_send_statistics():
    """
    Пример генерации и отправки статистики (вечером)
    """
    from statistics_generator import StatisticsGenerator
    import subprocess
    
    print("\n" + "="*60)
    print("📊 ГЕНЕРАЦИЯ И ОТПРАВКА СТАТИСТИКИ")
    print("="*60)
    
    # Генерируем статистику
    generator = StatisticsGenerator()
    
    # Текстовый отчет
    report = generator.generate_text_report()
    print("\n📄 ТЕКСТОВЫЙ ОТЧЕТ:")
    print(report)
    
    # Инфографика
    print("\n📈 ГЕНЕРАЦИЯ ИНФОГРАФИКИ...")
    image_file = generator.generate_infographic()
    
    if image_file:
        print(f"✅ Инфографика сохранена: {image_file}")
    
    # Отправка в Telegram
    print("\n📤 ОТПРАВКА В TELEGRAM...")
    subprocess.run(['python', 'send_daily_statistics.py'])


# ЗАПУСК ПРИМЕРОВ
if __name__ == "__main__":
    print("="*60)
    print("🔍 ПРИМЕР 1: АНАЛИЗ И ЛОГИРОВАНИЕ")
    print("="*60)
    
    logged_ids = example_analysis_with_logging()
    
    print("\n" + "="*60)
    print("📝 ПРИМЕР 2: ОБНОВЛЕНИЕ РЕЗУЛЬТАТОВ")
    print("="*60)
    
    # example_update_results()
    
    print("\n" + "="*60)
    print("📊 ПРИМЕР 3: ГЕНЕРАЦИЯ СТАТИСТИКИ")
    print("="*60)
    
    # example_generate_and_send_statistics()
    
    print("\n✅ ВСЕ ПРИМЕРЫ ВЫПОЛНЕНЫ!")

