"""Компактные банки фраз для MAX-постов.

Тон канала «Честная ставка»: спокойно, по-человечески, без давления «ставьте».
"""

from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROTATION_PATH = ROOT / "data" / "phrase_rotation.json"

DISCLAIMERS: list[str] = [
    "Ставки — это риск. Можно потерять деньги. Решайте сами и ставьте только лишние.",
    "Мы делимся анализом, а не гарантией. Ответственность за ставку — на вас.",
    "Это не совет «обязательно ставить». 18+. Играйте спокойно и без долгов.",
    "Спорт непредсказуем. Даже сильный разбор может ошибиться.",
    "Если ставки начинают мешать жизни — лучше остановиться. 18+.",
]

DISCIPLINE_TIPS: list[str] = [
    "Не пытайтесь сразу отыграться большей суммой — так чаще сливают банк.",
    "Лучше пропустить день без ставки, чем поставить «на авось».",
    "Держите размер ставки небольшим. Эмоции — плохой советчик.",
    "Одна ставка ничего не решает. Смотрим на серию и честный учёт.",
    "Зафиксируйте ставку у себя — так потом честнее смотреть результат.",
]

# Короткие пояснения без жаргона.
EDUCATION_TIPS: list[str] = [
    "Мы ставим не на «красивый матч», а только когда у букмекера хорошая цена.",
    "Высокий процент сам по себе не повод ставить: важна и цена коэффициента.",
    "День без ставки — норма. Молчать лучше, чем слабая ставка.",
    "Пока мало сыгранных сигналов — рано говорить «система в плюсе» или «в минусе».",
    "Маленькая доля банка нужна, чтобы пережить полосу неудач.",
]

CLOSING_PHRASES: list[str] = [
    "Разбираем честно. Решайте спокойно.",
    "Качество важнее количества ставок.",
    "Берегите банк и голову.",
    "Ваше спокойствие важнее любой ставки.",
]

ROTATING_TIPS: list[str] = DISCIPLINE_TIPS + EDUCATION_TIPS + CLOSING_PHRASES


class RotatingTips:
    """One short footer line per post; index persists between runs."""

    def __init__(self, path: Path | None = None):
        self.path = path or DEFAULT_ROTATION_PATH
        self._idx = 0
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._idx = 0
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._idx = 0
            return
        if isinstance(raw, dict):
            self._idx = int(raw.get("idx") or 0)
        else:
            self._idx = 0

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"idx": self._idx}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def next(self) -> str:
        if not ROTATING_TIPS:
            return ""
        tip = ROTATING_TIPS[self._idx % len(ROTATING_TIPS)]
        self._idx += 1
        self._save()
        return tip


def pick_disclaimer(*, rng: random.Random | None = None) -> str:
    r = rng or random
    return r.choice(DISCLAIMERS)


def pick_discipline(*, rng: random.Random | None = None) -> str:
    r = rng or random
    return r.choice(DISCIPLINE_TIPS)


def pick_education(*, rng: random.Random | None = None) -> str:
    r = rng or random
    return r.choice(EDUCATION_TIPS)


def pick_closing(*, rng: random.Random | None = None) -> str:
    r = rng or random
    return r.choice(CLOSING_PHRASES)


def format_footer(*, tip: str | None = None, rotator: RotatingTips | None = None) -> str:
    """Подвал поста: одна короткая фраза + дисклеймер."""
    line = tip if tip is not None else (rotator.next() if rotator else pick_closing())
    return f"{line}\n⚠️ {pick_disclaimer()}"
