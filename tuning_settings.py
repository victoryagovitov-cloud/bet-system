#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Гибкие настройки для управления количеством матчей и фильтрами.

Изменения собраны в отдельном файле, чтобы можно было быстро откатить
всё назад, просто вернув значения по умолчанию.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TuningSettings:
    # Сколько матчей публикуем за один прогон (по умолчанию было 5)
    max_matches: int = 7

    # Насколько расслаблены фильтры (1.0 = базовые; <1.0 = мягче; >1.0 = жёстче)
    filter_relaxation: float = 0.70

    # Нужна ли повторная проверка дедупликации перед отправкой (по умолчанию True)
    enable_secondary_dedup: bool = False

    # Целевой диапазон вероятности (в долях, т.е. 0.75 = 75%)
    probability_floor: float = 0.75
    probability_cap: float = 0.90

    # Отдельные настройки для баскетбола
    basketball_probability_floor: float = 0.70
    basketball_probability_cap: float = 0.88
    basketball_filter_relaxation: float = 0.65

    # Отдельные настройки для футбола
    football_probability_floor: float = 0.70
    football_probability_cap: float = 0.88

    # Отдельные настройки для тенниса
    tennis_probability_floor: float = 0.75
    tennis_probability_cap: float = 0.90

    # Параметры Telegram-отправки
    telegram_chunk_max_chars: int = 2800  # макс. длина одного сообщения
    telegram_chunk_pause_seconds: float = 2.0  # пауза между частями


SETTINGS = TuningSettings()

