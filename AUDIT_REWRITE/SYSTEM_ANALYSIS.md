# SYSTEM_ANALYSIS — Технический разбор старой системы

**Дата:** 2026-08-03  
**Проект:** `D:\cursor\Backtothestart` (TrueLiveBet / AI Prime)

---

## 1. Как было задумано

Система задумывалась как **PVO / «три радиуса»**:

| Радиус | Фаза | Частота (по CONTINUITY / docs) | Источник |
|---|---|---|---|
| Дальний | Prematch 2–7+ дней | 1–6 ч / 1× день | Scores24 + (позже) AI Prime |
| Средний | Prematch 0–24 ч | 10–30 мин | Scores24 / schedulers |
| Ближний | Live | 45 сек – 5 мин | HTML парсинг БК + Scores24 verify |

Цепочка ценности:
1. Собрать матчи и коэффициенты.
2. Нормализовать к одному `match_id`.
3. Посчитать доминирование / вероятность / EV.
4. (Опционально) спросить ИИ при значимом событии.
5. Отфильтровать → сформировать сигнал → опубликовать в Telegram `@TrueLiveBet`.
6. Закрыть результат → учиться на ошибках (adaptive thresholds / ML — частично).

На практике это **несколько параллельных архитектур**, живших одновременно:
- **Вариант A:** Scores24 GraphQL + Winline/Baltbet HTML collectors + Streamlit dashboard (`start_production_stack_v2*.bat`).
- **Вариант B:** AI Prime Parser через Perplexity/webhook (`ai_prime_*`, cron 9:00–00:00).
- **Вариант C:** Монолит `generate_live_report.py` как «мозг» live-канала.
- **Вариант D:** Prematch через API-Sport / `daily_predictions.py` + `TelegramPublisher`.

`CONTINUITY.md` отражает намерения; код содержит все варианты сразу → **drift**.

---

## 2. Как данные попадали в систему

```
[Bookmaker websites HTML/SPA]
        │  Browser MCP / MCP Proxy / Playwright-like snapshot
        ▼
src/stats/*_collector.py  OR  ai_prime_parser*_v2  OR  core/betboom_core
        │
        ├─► data/predictions.db   (snapshots, matches_master, odds)
        └─► data/betting_system.db (SQLAlchemy bets path)

[Scores24 GraphQL]
        │  scores24_graphql_client.py / football_*_collector
        ▼
live_snapshots / prematch_snapshots / xG / results

[AI APIs]
        │  Perplexity (legacy free-text JSON) + Claude Haiku via AITunnel
        ▼
match_ai_insights / signal_generator predictions
```

### Проблемы ingest
- HTML DOM менялся → коллекторы и autocorrector ломались.
- Perplexity как парсер видел статический HTML → неполные JSON.
- Нет единого event ID от БК → fuzzy matching по именам/лиге/времени.
- Две БД писали разные пайплайны без жёсткой синхронизации.

---

## 3. Как данные обрабатывались

### Нормализация матча
`src/tracking/match_id_generator.py`:
```
match_id = normalize(league)_normalize(home)_normalize(away)_YYYYMMDD
```
Плюс fuzzy `TeamNameResolver` (`src/matching/team_name_resolver.py`) для Scores24 ↔ БК.

### Live-метрики (футбол)
`graphql_live_analyzer.py` / `generate_live_report.py`:
- **Dominance** ≈ `ΔxG*3 + ΔSoT*2 + Δshots + Δposs*0.5 + (score_diff*2)*(minute/90)`
- **Probability estimate** ≈ эвристика от xG/SoT/shots/possession/score_gap
- **EV** = `(p * odds) - 1` (в % ×100)

### Handball
`src/handball/totals_calculator.py` — чистая проекция темпа:
```
pace = total/minute
projected = total + pace*(60-minute)
Over if projected ≥ 62; Under if ≤ 58; иначе skip (с 36-й минуты)
```

### Фильтрация (пример strict live football)
`match_pre_filters.py`:
- минута 20–85
- не проигрывает, lead < 3
- xG diff ≥ 0.4, xG total ≥ 0.6
- possession лидера ≥ 55%, SoT diff ≥ 2, SoT лидера ≥ 3, combined SoT ≥ 7
- exclude derby/cup/friendly (strict)

SAFE/RISKY/PRIMARY — `optimized_filters.py` (см. `REUSABLE_LOGIC.md`).

---

## 4. Как принимались решения

Многоуровнево (и местами конфликтующе):

1. **Hard filters** — отсекают матч.
2. **Ranking / diversity** — выбирают топ для поста (`generate_live_report`).
3. **Value/edge gate** — `edge = p - 1/odds`; signal `EV ≥ 5%`.
4. **AI consensus** (`signal_generator.py`) — Perplexity + Claude согласны по Over/Under, `|Δp| ≤ 0.15`, ensemble `0.55*perp + 0.45*claude`.
5. **Kelly + risk caps** — размер ставки (`src/risk/*`, `config/risk_limits.json`).
6. **AI trigger gate** — ИИ не на каждый тик: 15 мин / signature / line move ≥5% odds или ≥10% sentiment.

Стратегии `src/strategies/*` (BTTS, xG totals, comeback) в конфиге **выключены** (`enabled: false`) — скорее прототипы.

---

## 5. Как формировались сообщения Telegram

См. подробно `TELEGRAM_STRUCTURE.md`. Кратко:

| Канал публикации | Formatter | Стиль |
|---|---|---|
| Live multi-sport | `generate_live_report._format_match_block` | Нумерованный LIVE-АНАЛИЗ, xG блок, EV |
| Handball/signal | `signal_generator.format_signal_for_telegram` | Компактный EV-сигнал + AI consensus |
| Prematch | `telegram_publisher._format_prematch_message` | HTML `<b>`, П1/П2, EV |
| Daily | `daily_predictions.py` | Дневной отчёт |
| Фразы | `improve_telegram_messages.py` | random DISCLAIMER / CLOSING / DISCIPLINE |

Канон бренда: `MESSAGE_TEMPLATE_STANDARD.md` (разделители, эмодзи спорта, подвал TrueLiveBet).

---

## 6. Сильные архитектурные идеи

1. **Единый `match_id` через lifecycle** (pre → live → finished) — правильная модель для ML.
2. **Сбор без фильтров, фильтрация на анализе** — корректно для поиска edge и обучения.
3. **AI triggers + input_signature + throttle** — экономия токенов (~заявленные 91%).
4. **Structured outputs (Pydantic + JSON Schema)** для Claude — уход от хрупкого «ответь JSON».
5. **Чистые калькуляторы** (handball totals, Kelly, EV) — легко тестировать и переносить.
6. **Telegram phrase banks** — живой тон канала без хардкода одной фразы.
7. **Режимы риска** (conservative/standard/aggressive/fun_live) как конфиг.
8. **Scores24 GraphQL как verify/stats** — уже API-путь (частично).

---

## 7. Слабые места (без смягчения)

1. **Парсинг HTML как фундамент** — постоянный ремонт селекторов.
2. **Монолиты** (`generate_live_report.py`) смешивают всё.
3. **Root sprawl:** 682 py + 692 md — невозможно поддерживать.
4. **Dual DB + dual packages** (`strategy`/`strategies`, `analysis`/`analytics`, `mcp`/`mcp_server`).
5. **Config drift** порогов в 3+ местах.
6. **Secrets в коде** — security debt.
7. **Autocorrector пишет в `.py`** — самомодификация продакшена.
8. **Нет чёткого bounded context** ingest / domain / delivery.
9. **Документация врёт статусу** («100% production ready») при множестве недоделанных веток.
10. **Windows-only ops debt** (AHK, prevent Windows updates, десятки bat).

---

## 8. Что ломалось из-за парсинга

| Симптом | Причина |
|---|---|
| Пустые live списки | Смена CSS/SPA lazy-load |
| Неверные коэффициенты | Парсинг не того DOM-узла |
| AI Prime JSON без `matches` | Perplexity текст вместо JSON / markdown wrap |
| Пропуск топ-матчей | Лимиты токенов / неполный snapshot |
| Baltbet DISABLED | Коэффициенты не находятся |
| LigaStavok blocked | Антибот QAB |
| BetBoom минифицированные классы | Хрупкие селекторы |
| Autocorrector «чинит» не то | Эвристики по `collectors.json` |
| Дубли match_id | Разные написания команд/дат между источниками |
| Database locked | Параллельные collectors → SQLite |

Документированные фиксы: `CLAUDE.md` (полезно как каталог граблей).

---

## 9. Что сохранить в новой системе

- Модель lifecycle + детерминистический ID (доработать под API event IDs).
- Формулы: EV, edge, Kelly, handball totals, dominance (как опциональный feature).
- Таблицы порогов фильтров — как **config**, не как размазанный код.
- AI trigger policy (события + throttle + signature).
- Telegram template system + phrase banks.
- Risk modes + daily/match caps.
- Идея ensemble consensus (два независимых оценщика) — опционально, после числового ядра.
- Scores24/API-адаптеры как референс интеграции (не HTML).
- Исторические данные в `predictions.db` — **архив для backtest**, не runtime schema as-is.

---

## 10. Что удалить полностью

- `src/mcp/**`, `src/mcp_server/**`
- HTML collectors БК в `src/stats/*` (кроме API-based Scores24-логики, которую переписать)
- `auto_corrector*.py`
- AI Prime как **парсер страниц** (`ai_prime_parser*`, webhook parse endpoints, cron bat)
- Autoclicker / AHK / prevent_windows_updates как часть продукта
- Дубли analyzer/launcher поколений v1 после миграции идей
- Сотни одноразовых `check_/debug_/fix_` — в архив `archive/legacy_scripts/`
- Вторая БД как параллельная правда (слить или выкинуть)

---

## 11. Варианты трактовки архитектуры (не гадание)

### Трактовка 1 — «Data collection platform»
Фокус CONTINUITY: 30 дней сбора, ML потом.  
Аргументы: `start_production_stack*`, Streamlit, collectors, data quality validators.  
Минус: канал Telegram вторичен в этой трактовке.

### Трактовка 2 — «Telegram signal factory»
Фокус `generate_live_report` + templates + TrueLiveBet brand.  
Аргументы: MESSAGE_TEMPLATE_STANDARD, phrase banks, daily/live publishers.  
Минус: качество сигналов упиралось в парсинг.

### Трактовка 3 — «AI Prime harvest»
Фокус Perplexity JSON → DB → handball totals → later signals.  
Аргументы: `ai_prime_*`, handball calculator, PARSING_STRATEGY_V3.  
Минус: Perplexity как ingest — дорого и хрупко.

**Для новой системы:** взять **#2 как продукт** (Telegram signals) + **#1 как data/ML foundation**, но оба на **API ingest**. AI Prime (#3) оставить только как optional research layer, не как источник коэффициентов.

---

## 12. Вердикт

Старая система — **ценный прототип доменной логики**, обёрнутый в **неустойчивый ingest**.  
Переписывать нужно контур получения данных и границы модулей;  
сохранять — числовые правила, lifecycle, Telegram UX и risk/AI policies.
