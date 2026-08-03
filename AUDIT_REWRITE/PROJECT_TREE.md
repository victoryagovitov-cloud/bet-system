# PROJECT_TREE — Инвентаризация старого проекта Backtothestart

**Дата аудита:** 2026-08-03  
**Корень:** `D:\cursor\Backtothestart`  
**Масштаб:** ~682 `.py` в корне, ~110+ модулей в `src/`, ~692 `.md`, 43 `.bat`, 2 SQLite БД.

Игнорировано как шум: `node_modules`, `.git`, `__pycache__`, `.venv`, `venv`, `dist`, `build`.

---

## 1. Дерево (смысловое, не полный листинг 1000+ файлов)

```
Backtothestart/
├── src/                          # Основной пакет (целевая зона для переноса идей)
│   ├── ai/                       # AI-слой: триггеры, structured outputs, калибровка
│   ├── analysis/                 # multi_market_analyzer
│   ├── analytics/                # hybrid calibrator / stats
│   ├── bookmakers/               # availability checker
│   ├── data/                     # API adapters + scrapers (смесь API и HTML)
│   ├── db/                       # SQLAlchemy → betting_system.db (вторая БД)
│   ├── handball/                 # totals_calculator (чистая логика)
│   ├── learning/                 # auto_learner
│   ├── matching/                 # fuzzy team matching + aliases
│   ├── mcp/                      # Browser/MCP proxy для парсинга БК  [LEGACY]
│   ├── mcp_server/               # FastAPI MCP handlers              [LEGACY]
│   ├── ml/                       # features, train scripts, calibrate
│   ├── monitoring/               # health, auto_restart, autocorrector
│   ├── pipelines/                # prematch + telegram_publisher
│   ├── predictions/              # signal_generator
│   ├── risk/                     # Kelly + RiskManager
│   ├── stats/                    # коллекторы Scores24/BK           [LEGACY scraping]
│   ├── strategies/               # BTTS / xG totals / comeback
│   ├── strategy/                 # hybrid_bet_decider
│   ├── tracking/                 # predictions.db + match_id         [CRITICAL]
│   ├── utils/                    # team_translator, get_bookmaker_data
│   └── verification/             # pre_launch checks
├── core/                         # betboom_core / handball_core (AI Prime path)
├── data/                         # runtime DB + JSONL/CSV кеши
│   ├── predictions.db            # PRIMARY (~154 MB)
│   └── betting_system.db         # SECONDARY (~1 MB)
├── config/                       # strategy.json, risk_limits.json, collectors.json
├── backtest/                     # backtest_* против API-Sport
├── ai_prime/                     # sample JSON payloads
├── docs/                         # subscriber-facing docs
├── logs/                         # process logs
├── scripts/                      # browser MCP helpers + autostart docs
├── snapshots/                    # пусто (задумано под MCP snapshots)
├── telegram_failed_messages/     # failed Telegram dumps
├── AUDIT_REWRITE/                # этот аудит
├── *.bat / *.ps1                 # launchers / autostart / cron
├── ~682 root *.py                # one-off scripts, analyzers, tests, dashboards
└── ~692 root *.md                # статусы, чеклисты, инциденты, архитектура
```

---

## 2. Назначение крупных директорий

| Директория | Зачем | Вердикт для новой системы |
|---|---|---|
| `src/tracking/` | Единый match lifecycle + SQLite API | **Сохранить концепт** |
| `src/handball/` | Чистые формулы тоталов | **Портировать почти as-is** |
| `src/risk/` | Kelly + лимиты | **Портировать формулы** |
| `src/ai/` | Триггеры/structured outputs | **Рефактор, идея сильная** |
| `src/predictions/` | EV + consensus → Telegram | **Рефактор** |
| `src/pipelines/` | Telegram publisher | **Рефактор шаблонов** |
| `src/matching/` | Fuzzy matching команд | **Нужен, пока нет стабильных ID из API** |
| `src/stats/` | HTML/MCP коллекторы БК | **Удалить/архивировать** |
| `src/mcp/`, `src/mcp_server/` | Browser automation | **Удалить** |
| `core/` | Shared parse helpers AI Prime | **Удалить после миграции** |
| `data/` | БД и логи | **Архивировать данные; схему пересмотреть** |
| Root scripts | Хаос one-off | **Не переносить оптом** |

---

## 3. Категории файлов

### Парсинг (LEGACY — убрать из runtime)
- `src/stats/*_collector.py` (BetBoom/Winline/Baltbet/Melbet/Pari/LigaStavok)
- `src/mcp/*`, `src/mcp_server/*`
- `ai_prime_parser.py`, `ai_prime_parser_v2.py`, `fetch_perplexity_parsing.py`
- `core/betboom_core.py`, `src/data/betboom_scraper.py`
- `config/collectors.json` (CSS selector experiments)
- `src/monitoring/auto_corrector*.py` (переписывает селекторы в исходниках)

### Бизнес-логика (ценность)
- `match_pre_filters.py`, `optimized_filters.py`, `league_filter.py`
- `adaptive_filter_manager.py`, `adaptive_thresholds.json`
- `src/handball/totals_calculator.py`
- `src/strategy/hybrid_bet_decider.py`
- `src/strategies/{both_teams_score,xg_totals,favorite_comeback}.py`
- `graphql_live_analyzer.py` (+ копии `graphql_*_analyzer.py`)
- `generate_live_report.py` (монолит: фильтры + ranking + Telegram)

### Коэффициенты / edge / signals
- `src/predictions/signal_generator.py` — EV, AI consensus, min_ev=5%
- `src/risk/kelly.py`, `src/risk/manager.py`
- `config/strategy.json`, `config/risk_limits.json`
- `src/ai/ai_triggers.py` — throttle 15 мин, signature dedup
- `src/tracking/line_movement.py`

### Telegram
- `improve_telegram_messages.py` — DISCLAIMERS/CLOSING/DISCIPLINE banks
- `MESSAGE_TEMPLATE_STANDARD.md`, `TELEGRAM_TEMPLATES_REFERENCE.md`
- `src/pipelines/telegram_publisher.py`
- `src/predictions/signal_generator.py` (`format_signal_for_telegram`)
- `generate_live_report.py` (`_format_match_block`)
- `send_to_telegram.py`, `telegram_simple.py`, `daily_predictions.py`
- `telegram_report_*.txt`, `last_telegram_message.txt`

### Конфиги
- `.env`, `.env.example` (example неполный)
- `system_config.yaml`, `system_config.py`
- `config.json`, `mcp.json` (+ 2 варианта)
- `config/strategy.json`, `config/risk_limits.json`, `config/collectors.json`
- `adaptive_thresholds.json`, `src/matching/team_aliases.json`

### Логирование / мониторинг
- `logs/*`, `data/logs/*`
- `src/monitoring/health_check.py`, `auto_restart.py`, `process_manager.py`
- `system_logger.py` (root)

### Автозапуск / планировщики
- `ai_prime_cron.bat` + Task `AI Prime Cron`
- `start_daily_scheduler.bat` (+ Startup shortcut → `D:\cursor\!Backtothestart\...`)
- `setup_full_autostart.bat`, `install_autostart.bat`, `AUTOSTART_SETUP_NOW.bat`
- `prematch_scheduler.py`, `start_production_stack_v2*.bat`
- См. `AUTOSTART_AUDIT.md`

### Внешние интеграции
- Scores24 GraphQL (`scores24_graphql_client.py`, collectors)
- AITunnel / Claude Haiku (`src/ai/structured_client.py`)
- Perplexity (`perplexity_analyzer.py`, `fetch_perplexity_parsing.py`)
- API-Sport (`src/data/api_sport_adapter.py`, `backtest/*`)
- Telegram Bot API
- MCP Browser proxy (localhost:8765 / 8001)

### БД / кеши
| Путь | Роль |
|---|---|
| `data/predictions.db` | Primary lifecycle (~154 MB) |
| `data/betting_system.db` | SQLAlchemy bets/settlement |
| `data/*.jsonl` | odds delay, predictions logs |
| `data/teams_database.json`, `players_database.json` | справочники |
| `data/recommendations_log.csv` | история рекомендаций |

### Тесты / устаревшее / мусор
- ~137 root `test_*.py` + `test_runner.py`
- Сотни `check_*.py`, `debug_*.py`, `fix_*.py`
- v1/v2 дубли launchers и MCP clients
- ~600+ статусных `.md` без архитектурной ценности
- AHK/autoclicker (`working_autoclicker.py`, `start_working_autoclicker.bat`)

---

## 4. Критически важные файлы

| Файл | Почему |
|---|---|
| `src/tracking/match_id_generator.py` | Детерминистический lifecycle ID |
| `src/tracking/predictions_db.py` | Схема и доступ к primary DB |
| `src/handball/totals_calculator.py` | Готовая числовая стратегия |
| `src/risk/kelly.py` | Чистая формула стейка |
| `src/ai/ai_triggers.py` | Антиспам AI-вызовов |
| `src/predictions/signal_generator.py` | EV + consensus + TG format |
| `improve_telegram_messages.py` | Банки фраз канала |
| `MESSAGE_TEMPLATE_STANDARD.md` | Канон структуры постов |
| `match_pre_filters.py` / `optimized_filters.py` | Пороговые таблицы live |
| `config/strategy.json` / `config/risk_limits.json` | Режимы риска |
| `generate_live_report.py` | Фактический production-орchestrator (но монолит) |

---

## 5. Дубли

| Кластер | Комментарий |
|---|---|
| `ai_prime_parser.py` vs `ai_prime_parser_v2.py` | Два поколения парсера |
| `start_production_stack.bat` / `_v2` / `_debug` / `_optimized` | 4 поколения стека |
| `browser_mcp_client.py` vs `_v2`; `betboom_mcp_client` vs `betboom_client_v2` | MCP forks |
| `results_collector.py` vs `_v2` | Results path split |
| `src/mcp/` vs `src/mcp_server/` | Две MCP-поверхности |
| `src/strategy/` vs `src/strategies/` | Naming collision |
| `src/analysis/` vs `src/analytics/` | Параллельные пакеты |
| `predictions.db` vs `betting_system.db` | Две БД без единой модели |
| 8× `graphql_*_analyzer.py` | Копипаста по видам спорта |
| 3+ Telegram formatters | live_report / signal_generator / daily_predictions / publisher |

---

## 6. Legacy / неиспользуемое / опасное

### Legacy
- Весь HTML/MCP scraping слой
- Autocorrector, который патчит CSS-селекторы в `.py`
- Perplexity-as-parser (использовать только как research, не как ingest)
- AHK autoclicker путь

### Неиспользуемое / сомнительное (UNCONFIRMED без runtime-трассировки)
- Strategies в `config/strategy.json` все `enabled: false`
- Baltbet collector (в CONTINUITY помечен DISABLED, код остаётся)
- `snapshots/` пустая
- Сотни one-off root scripts без импортов из production bats

### Опасные места
1. **Hardcoded API/Telegram keys** в исходниках (`system_config.yaml`, analyzers, backtest, publishers) — ротация обязательна.
2. **`generate_live_report.py` (~4.6–4.8k LOC)** — сильная связность: фильтры + AI + ranking + Telegram.
3. **Dual threshold drift:** `system_config.yaml` ≠ `optimized_filters.py` ≠ `adaptive_thresholds.json`.
4. **SQLite multi-writer** без строгой очереди (WAL помогает, но не архитектура).
5. **Autocorrector переписывает код коллекторов** — хрупкость максимальная.
6. **Fuzzy match_id** зависит от нормализации названий → дубликаты при расхождении источников.
7. Shortcut Startup указывал на `D:\cursor\!Backtothestart\` (другой путь) — рассинхрон копий проекта.

### Места сильной связности
```
Collectors (MCP/HTML)
    → predictions_db / betting_system.db
        → generate_live_report / signal_generator / daily_predictions
            → TelegramPublisher / send_to_telegram
                → improve_telegram_messages phrase banks

AI path: collectors → ai_triggers → ai_service → structured_client → match_ai_insights
```

Любой слом селектора или DOM рвал весь пайплайн.

---

## 7. Важные root-скрипты (не полный список)

| Файл | Назначение |
|---|---|
| `generate_live_report.py` | Главный live-анализ + Telegram |
| `ai_prime_webhook.py` | Flask webhook AI Prime |
| `ai_prime_parser(_v2).py` | JSON → DB |
| `daily_predictions.py` / `daily_picks.py` | Prematch публикации |
| `streamlit_dashboard.py` / `dashboard.py` | Мониторинг UI |
| `prematch_scheduler.py` | Планировщик prematch |
| `graphql_live_analyzer.py` | Live метрики (dominance, filters) |
| `match_pre_filters.py` | Strict/soft live filters |
| `optimized_filters.py` | SAFE/RISKY/PRIMARY thresholds |
| `improve_telegram_messages.py` | Phrase banks |
| `scores24_graphql_client.py` | Scores24 API client (уже не HTML БК) |

---

## 8. Вывод по дереву

Проект — **два слоя**:
1. Относительно осмысленный пакет `src/` + конфиги + Telegram-шаблоны.
2. Огромный плоский слой root-скриптов и markdown-статусов (технический долг).

Для новой системы брать **не репозиторий целиком**, а **выжимку модулей и правил** из разделов 4–5 + документы `REUSABLE_LOGIC.md` / `TELEGRAM_STRUCTURE.md`.
