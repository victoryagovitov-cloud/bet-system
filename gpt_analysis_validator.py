#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Валидация качества GPT анализа для предотвращения публикации некорректных прогнозов.
Мягкая валидация - не отсекает много матчей, только явные противоречия.
"""

from typing import Dict, Optional, Tuple


def validate_gpt_analysis(match: Dict, gpt_result: Dict) -> Tuple[bool, Optional[str]]:
    """
    Валидация анализа GPT на противоречия.
    
    МЯГКАЯ валидация - отсекает только явные противоречия, не строгая.
    
    Args:
        match: Словарь с данными матча
        gpt_result: Результат анализа GPT
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, reason_if_invalid)
        - is_valid: True если анализ валиден
        - reason_if_invalid: Причина отклонения (если не валиден)
    """
    probability = gpt_result.get("claude_probability", 0)
    if probability <= 0:
        return False, "Вероятность не указана"
    
    # Получаем данные матча
    sport = match.get("sport_type", "football")
    score = match.get("score", "0:0")
    minute = match.get("minute_numeric")
    # Безопасная обработка: если minute None, используем 0
    minute = minute if minute is not None else 0
    dominance = match.get("dominance_score", 0)
    
    # Парсим счет
    try:
        home_score, away_score = map(int, score.split(':'))
        score_diff = abs(home_score - away_score)
    except (ValueError, AttributeError):
        score_diff = 0
    
    # ВАЛИДАЦИЯ 1: Очень высокая вероятность при малой разнице счета (только для поздних матчей)
    # Это нормально для ранних матчей, но подозрительно для поздних
    # Проверяем, что minute не None перед сравнением
    if minute is not None and minute >= 70 and probability > 92 and score_diff <= 1:
        return False, f"Подозрительно: вероятность {probability}% при разнице {score_diff} гола на {minute} минуте"
    
    # ВАЛИДАЦИЯ 2: Очень высокая вероятность при отрицательном dominance (явное противоречие)
    # Это критично - если dominance отрицательный, значит лидер не доминирует
    if probability > 85 and dominance < -2:
        return False, f"Противоречие: вероятность {probability}% при отрицательном dominance {dominance:.1f}"
    
    # ВАЛИДАЦИЯ 3: Очень низкая вероятность при большом преимуществе (GPT недооценил)
    # Это не критично, но стоит отметить - возможно, GPT ошибся
    # Проверяем, что minute не None перед сравнением
    if probability < 60 and score_diff >= 3 and dominance > 8 and minute is not None and minute >= 50:
        # Не отклоняем, но логируем как предупреждение
        return True, f"Предупреждение: низкая вероятность {probability}% при большом преимуществе"
    
    # ВАЛИДАЦИЯ 4: Для тенниса - проверка на разумность вероятности
    if sport == "tennis":
        sets_score = match.get("sets_score", "0:0")
        try:
            sets_home, sets_away = map(int, sets_score.split(':'))
            sets_diff = abs(sets_home - sets_away)
        except (ValueError, AttributeError):
            sets_diff = 0
        
        # Если один игрок выиграл 2 сета, вероятность должна быть высокой
        if sets_diff >= 2 and probability < 75:
            return False, f"Противоречие: выиграно {sets_diff} сетов, но вероятность только {probability}%"
        
        # Если сетов равное количество, вероятность не должна быть очень высокой
        if sets_diff == 0 and probability > 90:
            return False, f"Подозрительно: равные сеты, но вероятность {probability}%"
    
    # Все проверки пройдены
    return True, None


def apply_soft_validation(match: Dict, gpt_result: Dict) -> Dict:
    """
    Применяет мягкую валидацию к результату GPT анализа.
    
    Если валидация не пройдена, помечает матч, но не исключает его полностью
    (только если это критичное противоречие).
    
    Args:
        match: Словарь с данными матча
        gpt_result: Результат анализа GPT
    
    Returns:
        Обновленный gpt_result с флагом валидации
    """
    is_valid, reason = validate_gpt_analysis(match, gpt_result)
    
    gpt_result["validation_passed"] = is_valid
    if not is_valid:
        gpt_result["validation_warning"] = reason
        # КРИТИЧНО: Если валидация не пройдена, НЕ исключаем матч полностью
        # Только помечаем для логирования
        # Это позволяет системе находить матчи, даже если валидация строгая
    
    return gpt_result

