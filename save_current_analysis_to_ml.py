# -*- coding: utf-8 -*-
"""
💾 Сохранение текущего анализа в ML формат
"""
import sys
import io
from prediction_logger_ml import PredictionLoggerML

# Настройка UTF-8 для вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logger = PredictionLoggerML()

print("🤖 Сохранение матчей для ML...\n")

# МАТЧ 1: Дженоа - Кремонезе
match1 = {
    'sport': 'football',
    'team1': 'Дженоа',
    'team2': 'Кремонезе',
    'league': 'Серия B',
    'score': '0:2',
    'time': '2Т, 81 мин',
    'odds': 1.01,
    'category': 'perfect'
}

scores24_stats1 = {
    'match_stats': {
        'xg': {'team1': 0.54, 'team2': 1.52},
        'possession': {'team1': 51, 'team2': 49},
        'shots': '9 - 12',
        'shots_on_target': None,
        'corners': None
    },
    'h2h': None,
    'form': None
}

pred_id1 = logger.add_prediction_ml(match1, scores24_stats1)
print(f"✅ МАТЧ 1 сохранен: ID #{pred_id1}")

# МАТЧ 2: Вулверхэмптон - Челси
match2 = {
    'sport': 'football',
    'team1': 'Вулверхэмптон',
    'team2': 'Челси',
    'league': 'Кубок лиги',
    'score': '2:3',
    'time': '2Т, 86 мин',
    'odds': 1.25,
    'category': 'perfect'
}

scores24_stats2 = {
    'match_stats': {
        'xg': {'team1': 1.03, 'team2': 2.29},
        'possession': {'team1': 39, 'team2': 61},
        'shots': '13 - 9',
        'shots_on_target': None,
        'corners': None
    },
    'h2h': None,
    'form': None
}

pred_id2 = logger.add_prediction_ml(match2, scores24_stats2)
print(f"✅ МАТЧ 2 сохранен: ID #{pred_id2}")

# МАТЧ 3: Суонси Сити - Манчестер Сити
match3 = {
    'sport': 'football',
    'team1': 'Суонси Сити',
    'team2': 'Манчестер Сити',
    'league': 'Кубок Английской лиги',
    'score': '1:2',
    'time': '2Т, 89 мин',
    'odds': 1.08,
    'category': 'perfect'
}

scores24_stats3 = {
    'match_stats': {
        'xg': {'team1': 0.13, 'team2': 1.34},
        'possession': {'team1': 23, 'team2': 77},
        'shots': '2 - 23',
        'shots_on_target': None,
        'corners': None
    },
    'h2h': None,
    'form': None
}

pred_id3 = logger.add_prediction_ml(match3, scores24_stats3)
print(f"✅ МАТЧ 3 сохранен: ID #{pred_id3}")

# МАТЧ 4: Ньюкасл Юнайтед - Тоттенхэм
match4 = {
    'sport': 'football',
    'team1': 'Ньюкасл Юнайтед',
    'team2': 'Тоттенхэм',
    'league': 'Кубок Английской лиги',
    'score': '2:0',
    'time': '2Т, 74 мин',
    'odds': 1.03,
    'category': 'perfect'
}

scores24_stats4 = {
    'match_stats': {
        'xg': {'team1': 1.28, 'team2': 0.62},
        'possession': {'team1': 48, 'team2': 52},
        'shots': '9 - 10',
        'shots_on_target': None,
        'corners': None
    },
    'h2h': None,
    'form': None
}

pred_id4 = logger.add_prediction_ml(match4, scores24_stats4)
print(f"✅ МАТЧ 4 сохранен: ID #{pred_id4}")

# МАТЧ 5: Фортуна Дюссельдорф - Фрайбург
match5 = {
    'sport': 'football',
    'team1': 'Фортуна Дюссельдорф',
    'team2': 'Фрайбург',
    'league': 'Кубок Германии',
    'score': '1:2',
    'time': '2Т, 88 мин',
    'odds': 1.16,
    'category': 'medium_risk'
}

scores24_stats5 = {
    'match_stats': {
        'xg': {'team1': 1.52, 'team2': 1.46},
        'possession': {'team1': 59, 'team2': 41},
        'shots': '16 - 16',
        'shots_on_target': None,
        'corners': None
    },
    'h2h': None,
    'form': None
}

pred_id5 = logger.add_prediction_ml(match5, scores24_stats5)
print(f"✅ МАТЧ 5 сохранен: ID #{pred_id5}")

# МАТЧ 6: Страсбург - Осер
match6 = {
    'sport': 'football',
    'team1': 'Страсбург',
    'team2': 'Осер',
    'league': 'Первая лига',
    'score': '3:0',
    'time': '2Т, 70 мин',
    'odds': 1.02,
    'category': 'perfect'
}

scores24_stats6 = {
    'match_stats': {
        'xg': {'team1': 2.94, 'team2': 0.26},
        'possession': {'team1': 69, 'team2': 31},
        'shots': '13 - 5',
        'shots_on_target': None,
        'corners': None
    },
    'h2h': None,
    'form': None
}

pred_id6 = logger.add_prediction_ml(match6, scores24_stats6)
print(f"✅ МАТЧ 6 сохранен: ID #{pred_id6}")

# МАТЧ 7: Нант - Монако
match7 = {
    'sport': 'football',
    'team1': 'Нант',
    'team2': 'Монако',
    'league': 'Первая лига',
    'score': '2:3',
    'time': '2Т, 67 мин',
    'odds': 1.25,
    'category': 'perfect'
}

scores24_stats7 = {
    'match_stats': {
        'xg': {'team1': 0.96, 'team2': 3.06},
        'possession': {'team1': 46, 'team2': 54},
        'shots': '10 - 13',
        'shots_on_target': None,
        'corners': None
    },
    'h2h': None,
    'form': None
}

pred_id7 = logger.add_prediction_ml(match7, scores24_stats7)
print(f"✅ МАТЧ 7 сохранен: ID #{pred_id7}")

print(f"\n📊 Всего прогнозов в базе: {len(logger.predictions['predictions'])}")
print("✅ Данные сохранены для ML!")
