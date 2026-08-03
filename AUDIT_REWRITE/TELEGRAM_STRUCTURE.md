# TELEGRAM_STRUCTURE — Структура сообщений и шаблоны

**Исторический канал:** Telegram `@TrueLiveBet`  
**Целевой канал доставки:** **Max Messenger** (тот же контент/UX; меняется только publisher)  
**Дата извлечения:** 2026-08-03 (обновлено: pivot на Max)

> Этот документ описывает **формат и phrase banks**.  
> Транспорт: `delivery/max/` в `NEW_ARCHITECTURE_DRAFT.md`. Env: `MAX_BOT_TOKEN`, `MAX_CHAT_ID`.

---

## 1. Источники шаблонов (файлы)

| Путь | Что содержит |
|---|---|
| `MESSAGE_TEMPLATE_STANDARD.md` | Каноническая структура LIVE-постов |
| `TELEGRAM_TEMPLATES_REFERENCE.md` | Сводка + пример handball signal |
| `improve_telegram_messages.py` | `DISCLAIMERS_EXPANDED` (100+), `CLOSING_PHRASES_EXPANDED` (50+), `DISCIPLINE_TIPS_EXPANDED` (80+) |
| `src/pipelines/telegram_publisher.py` | Prematch/daily HTML formatter + send |
| `src/predictions/signal_generator.py` | `format_signal_for_telegram()` |
| `generate_live_report.py` | `_format_match_block()` + report envelope |
| `daily_predictions.py` | Дневные прогнозы |
| `send_to_telegram.py`, `telegram_simple.py` | Тонкие обёртки отправки |
| `telegram_report_*.txt`, `last_telegram_message.txt` | Реальные примеры |
| `telegram_failed_messages/` | Failed payloads |
| Env | `TLB_TELEGRAM_BOT_TOKEN`, `TLB_TELEGRAM_CHAT_ID` |

---

## 2. Канон структуры (`MESSAGE_TEMPLATE_STANDARD.md`)

### Заголовок
```
🎯 LIVE-ПРЕДЛОЖЕНИЯ НА (ЧЧ:ММ МСК, ДД.ММ.ГГГГ) 🎯
```

### Блок спорта
```
—————————————
⚽ ФУТБОЛ ⚽   |  🎾 ТЕННИС 🎾  |  🤾 ГАНДБОЛ 🤾
—————————————
```

### Карточка матча (стандарт)
```
N. {sport_emoji} Команда А – Команда Б
🏟️ Счет: X:Y (ММ')
✅ Ставка: П1/П2/X | Победа | ТБ/ТМ
📊 Кэф: X.XX
📌 Объяснение логики
```

### Подвал
```
——————————————————
💎 TrueLiveBet – Команда экспертов всегда на Вашей стороне! 💎

⚠️ Дисклеймер: ...
```

### Правила канона
- Нумерация матчей
- Полные имена команд
- Эмодзи вида спорта
- Разделители `—————`
- Без markdown `**` / сложных рамок в «стандарте»
- Объяснение через `📌`

> **Конфликт:** production `generate_live_report` и `telegram_publisher` используют HTML `<b>` и другой набор эмодзи. В новой системе нужно **явно выбрать один renderer**.

---

## 3. Production Live block (`generate_live_report.py`)

Фактический формат карточки:
```
{n}. [!повтор! ]🎯 <b>Home</b> - <b>Away</b>
🏟️ {country} • {tournament}
📊 Счет: {score} ({minute}') • {П1|П2} <b>{leader}</b>
📈 <b>xG:</b> … • <b>удары</b> … • <b>створ</b> … • <b>владение</b> …
🎯 {analysis}[🤖 CHAT GPT ИИ: …]
⚡ <b>ВЕРОЯТНОСТЬ: ~N%</b>
💰 Коэффициент: … | EV: ±N%
```

Envelope:
- Header: `🎯 LIVE-АНАЛИЗ • HH:MM МСК, DD.MM.YYYY`
- Sport sections + separators
- Footer: random DISCIPLINE → `@TrueLiveBet` closing → random DISCLAIMER

Dedup: slug матча за `DEDUPLICATION_HOURS` (default 4h) → drop или `!повтор!`.

---

## 4. Signal template (handball / EV) — самый удачный компактный формат

Из `signal_generator.py` + `TELEGRAM_TEMPLATES_REFERENCE.md`:

```
{🟢|🟡|🔵} 🏐 {Home}-{Away} ({score}, {min} мин)

📊 ТБ|ТМ {line} @{odds}
💰 EV: +{ev}%
📈 Вероятность: {p}%
🤝 Согласие ИИ: ✅ (Perplexity + Claude)

💡 {reasoning short}

{DISCIPLINE_TIP}

{CLOSING_PHRASE}

{DISCLAIMER}
```

**EV emoji mapping:**
- EV ≥ 10% → 🟢
- EV ≥ 5% → 🟡
- иначе → 🔵

**Почему удачный:** короткий, числовой, читается с телефона за 2 секунды, дисциплина+дисклеймер внизу.

---

## 5. Prematch (`telegram_publisher.py`)

Элементы:
- Команды (через `team_translator`)
- Страна • лига
- Время/дата
- Ставка П1/П2/X с `<b>`
- Model probability %, EV
- AI reasoning
- Random phrase banks

Формула EV в publisher: `(model_prob * odds) - 1`.

---

## 6. Phrase banks (`improve_telegram_messages.py`)

| Банк | Назначение | Кол-во |
|---|---|---|
| `DISCLAIMERS_EXPANDED` | Юр./ответственность | 100+ |
| `CLOSING_PHRASES_EXPANDED` | Закрытие + бренд | 50+ |
| `DISCIPLINE_TIPS_EXPANDED` | Банк-менеджмент, анти-догон | 80+ |

Использование: `random.choice(...)` в каждом посте → ощущение «живого» канала.

**Перенос:** вынести в `content/phrases/*.yaml` или JSON, без логики отправки.

Примеры дисциплины (сохранить тон):
- «Поддерживай дисциплину банка: те же 2% на сигнал, без догонов.»
- «Проиграл? Пауза. Не надо сразу отыгрываться.»

---

## 7. Лучшие примеры (файлы)

1. **Компактный сигнал** — `TELEGRAM_TEMPLATES_REFERENCE.md` (Швеция–Бразилия, ТБ 55.5, EV +12%).
2. **Канон LIVE** — `MESSAGE_TEMPLATE_STANDARD.md` (пример 08:50 МСК).
3. **Реальный live** — `last_telegram_message.txt` (Боде Глимт vs Брюн).
4. **Расширенный анализ** — `telegram_report_final_23_36.txt` (категории ⭐, дисклеймер).

---

## 8. Что было самым удачным

| Элемент | Оценка | Почему |
|---|---|---|
| Компактный EV-сигнал | ★★★★★ | Числа первыми, мало шума |
| Phrase banks + ротация | ★★★★★ | Тон канала, анти-шаблонность |
| Разделители по видам спорта | ★★★★☆ | Сканируемость |
| Канон MESSAGE_TEMPLATE_STANDARD | ★★★★☆ | Единый brand language |
| Длинный xG-блок live_report | ★★★☆☆ | Информативно, но тяжело в ленте |
| HTML `<b>` вперемешку с «без markdown» правилом | ★☆☆☆☆ | Конфликт стандартов |
| Упоминание «CHAT GPT» в live блоке | ★☆☆☆☆ | Устарело / бренд-шум |

---

## 9. Как перенести почти без потери качества

### Новый модуль `delivery/telegram/`
```
renderer.py          # один MessageRenderer
templates/
  live_card.j2       # или чистый Python dataclass → str
  signal_card.j2
  prematch_card.j2
  daily_report.j2
phrases/
  disclaimers.json
  closings.json
  discipline.json
publisher.py         # Bot API send + retry + failed dump
dedup.py             # match_key + TTL hours
```

### Контракт данных для renderer (без парсинга)
```python
@dataclass
class SignalView:
    sport: str
    home: str
    away: str
    score: str | None
    minute: int | None
    market: str          # "П1" | "ТБ 55.5" | ...
    odds: float
    probability: float   # 0..1 or %
    ev_pct: float
    reasoning: str
    consensus: str | None
    is_repeat: bool = False
```

### Правила переноса
1. **Один** визуальный стандарт (рекомендация: компактный signal + секции спорта для дайджестов).
2. Phrase banks — copy verbatim.
3. EV/вероятность/коэф — всегда в фиксированном порядке.
4. Dedup 4h + пометка повтора — сохранить.
5. HTML parse_mode согласовать один раз (HTML **или** plain).
6. Убрать «CHAT GPT» branding; опционально «ИИ» только при реальном AI-блоке.
7. Failed messages directory — сохранить как ops-паттерн.

---

## 10. Рекомендуемый целевой формат (API-era)

**Одиночный сигнал (push):**
```
🟢 ⚽ Home – Away (1:0, 67')

📊 П1 @1.42
💰 EV: +8.3%
📈 Модель: 76%
📌 Лидер по xG и ударам в створ, держит счет

📊 2% банка, без догона.
🤖 @TrueLiveBet
⚠️ …disclaimer…
```

**Дайджест (batch):** заголовок + секции спорта из канона + те же карточки укорочено.
