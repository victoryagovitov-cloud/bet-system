# NEW_ARCHITECTURE_DRAFT — API вместо парсинга

**Дата:** 2026-08-03 (обновлено: Max + API-Sport)  
**Продукт:** TrueLiveBet signals + data/ML foundation  
**Принцип:** числа, события, коэффициенты, правила — без DOM букмекеров.

### Messaging pivot

- Старый основной канал: Telegram `@TrueLiveBet` (в РФ de-facto недоступен).
- Новый основной канал: **Max Messenger bot** (тот же бренд/UX сигналов).
- Сохраняем: компактный EV-сигнал; discipline/disclaimer phrase banks; dedup/anti-spam; risk caps.
- Меняем: `delivery/telegram` → `delivery/max`; Bot API client; env `MAX_BOT_TOKEN` / `MAX_CHAT_ID` (вместо `TLB_TELEGRAM_*`).
- Цель: опыт TrueLiveBet живёт в Max, без зависимости от Telegram в hot path.
- Детали формата: `TELEGRAM_STRUCTURE.md` (контент) + этот файл §8 (транспорт).

### Data provider (закрыто)

- **Primary:** [API-Sport.ru](https://docs.api-sport.ru/) — контракт в `API_SPORT_CONTRACT.md`.
- Match.id = primary event id; `oddsBase` + `oddsBk` (betboom/pari/melbet/marathon).
- **MVP scope (закрыто, 2026-08-03):**
  - sport: **football only**
  - phase: **prematch only** (не live)
  - leagues: **только известные / топ-лиги** (allowlist по `tournament.id`)
  - handball / live / multi-sport — **вне MVP**

---

## 1. Старые модули, которые не нужны

| Старый модуль | Почему убрать |
|---|---|
| `src/mcp/**`, `src/mcp_server/**` | Browser automation |
| `src/stats/{betboom,winline,baltbet,melbet,pari,ligastavok}_*` | HTML collectors |
| `auto_corrector*.py` | Патч селекторов |
| `ai_prime_parser*`, webhook parse endpoints | Perplexity-as-scraper |
| `core/betboom_core.py` | Parse helpers |
| `config/collectors.json` | CSS experiments |
| AHK / autoclicker / prevent_windows_updates | Ops-костыли парсинговой эры |
| Множественные root analyzers-копии | Техдолг |

**Оставить как референс (не runtime):** Scores24 GraphQL client идеи, API-Sport adapter, phrase banks, domain formulas.

---

## 2. Новые модули

```
new_system/
  ingest/                 # API clients + normalized events
    providers/
      api_sport.py        # PRIMARY — docs.api-sport.ru
    poller.py             # REST poll MVP
    ws_consumer.py        # optional WebSocket match_snapshot/delta
    raw_store.py          # append-only raw payloads
  normalize/
    events.py             # Event, Fixture, Participants
    markets.py            # Market, Outcome, OddsQuote (oddsBase/oddsBk)
    mapping.py            # provider IDs ↔ internal IDs
  domain/                 # pure logic (из REUSABLE_LOGIC)
    filters/
    metrics/
    signals/
    risk/
  apps/
    signal_engine.py      # rules → SignalCandidate
    ai_enricher.py        # optional, trigger-gated
  delivery/
    max/                  # PRIMARY messaging (Max Messenger)
      renderer.py         # тот же SignalView / EV-формат
      publisher.py        # Max Bot API
      phrases/            # JSON из improve_telegram_messages
    # telegram/           # optional/archive — не hot path
  storage/
    db/                   # ONE schema
    cache/                # redis optional
  workers/
    ingest_worker.py
    signal_worker.py
    settle_worker.py
    publish_worker.py
  api/                    # optional internal admin/health
  configs/
    filters.yaml
    risk.yaml
    sports.yaml
    delivery.yaml         # channel_type: max
```

---

## 3. Pipeline новой системы

```
API-Sport REST (football, status=notstarted, date range)
   │  poll by days_ahead
   ▼
RawStore (append-only)
   ▼
Normalizer → Event + OddsQuote
   ▼
League allowlist gate (known/top tournament.id)
   ▼
Prematch Feature Builder (form/H2H optional later; odds + basic meta first)
   ▼
Filter Gate (odds band, min EV, risk mode)
   ▼
Signal Engine (p model OR heuristic → EV/edge → Kelly)
   │
   ├─(optional later) AI Enricher
   ▼
Dedup / Anti-spam / Risk caps
   ▼
Message Renderer → Max Publisher
   ▼
Settlement Worker (finished) → feedback
```

Ключ: **только football prematch в allowlist-лигах**. Live WS / handball / multi-sport — не в MVP.

---

## 4. Получение данных из API

Минимальный контракт провайдера:
```python
class OddsEventsProvider(Protocol):
    def list_live_events(self, sports: list[str]) -> list[RawEvent]: ...
    def get_odds(self, event_id: str, markets: list[str]) -> list[RawQuote]: ...
    def get_event_stats(self, event_id: str) -> RawStats: ...  # xG/SoT if available
    def get_results(self, since: datetime) -> list[RawResult]: ...
```

**Выбор зафиксирован:** API-Sport.ru (REST + WebSocket).  
Подробный контракт полей/auth/sportSlug: `API_SPORT_CONTRACT.md`.

Рекомендации:
- Primary уже даёт events + stats + oddsBase/oddsBk → отдельный stats-провайдер **не нужен**, пока ключи `matchStatistics` покрывают фильтры.
- Никакого Browser MCP в hot path.
- Таймстемпы всегда UTC + отдельное поле `received_at`.
- Prefer `oddsBk.betboom`, fallback другие BK / `oddsBase`.

---

## 5. Хранение сырых данных

Append-only:
```
raw_ingest(
  id, provider, endpoint, payload_json,
  fetched_at_utc, content_hash
)
```
Зачем: отладка, replay, споры «что видел бот», обучение.

Не парсить raw повторно в бизнес-логике — только через Normalizer в typed tables.

---

## 6. Нормализация сущностей

### Сущности
| Entity | Ключевые поля |
|---|---|
| `Sport` | code = API sportSlug (`football`, `tennis`, …) |
| `Competition` | `tournament.id` + translations.ru |
| `Team` | `homeTeam.id` / `awayTeam.id` + translations.ru |
| `Event` | `Match.id` as provider_event_id; status map notstarted→pre, inprogress→live, finished→finished |
| `ScoreState` | homeScore/awayScore + currentMatchMinute/Second |
| `Market` | type from oddsBase/oddsBk name/group/period + line |
| `OddsQuote` | selection, odds, bookmaker, source oddsBase\|oddsBk, ts |
| `FeatureSnapshot` | from matchStatistics + liveEvents-derived flags |
| `Signal` | event_id, market, selection, p, odds, ev, stake_pct, status |
| `Publication` | signal_id, **max_message_id**, rendered_text, published_at, channel=`max` |
| `Settlement` | signal_id, result, pnl |

### ID strategy
1. Primary: `api_sport` + `Match.id` (int).
2. Fallback human key: старый `match_id_generator` normalize (архив/legacy join).
3. Cross-provider map — только если появится второй provider.

---

## 7. Сигналы только на числах

```python
def evaluate_event(snapshot: FeatureSnapshot, quotes: list[OddsQuote], cfg) -> list[SignalCandidate]:
    if not pass_filters(snapshot, cfg.filters):
        return []
    p = estimate_probability(snapshot, cfg.model)   # heuristic or ML
    for q in select_markets(quotes, cfg.markets):
        ev = (p * q.odds - 1) * 100
        edge = p - 1/q.odds
        if ev < cfg.min_ev_pct:
            continue
        stake = apply_risk(kelly(p, q.odds), cfg.risk)
        yield SignalCandidate(...)
```

Football **prematch** — плагин `domain/sports/football_prematch.py` (MVP).  
Live football filters / handball totals / multi-sport — **вне MVP** (код legacy только как архив идей).

AI — optional later; не источник коэффициентов.

---

## 8. Delivery: Max (не Telegram)

`Signal` → `SignalView` DTO → `delivery/max/renderer.py` (контент из `TELEGRAM_STRUCTURE.md`) → `delivery/max/publisher.py`.

Сохранить:
- phrase banks (перенос JSON as-is)
- EV emoji thresholds (🟢/🟡/🔵)
- sport sections для digest
- dedup 4h
- failed message dump (`max_failed_messages/`)

`configs/delivery.yaml`:
```yaml
channel_type: max
dedup_hours: 4.0
# tokens only via env: MAX_BOT_TOKEN, MAX_CHAT_ID
```

Убрать зависимость renderer от collectors/DB ORM monolith.  
Telegram client — не в MVP runtime.

---

## 9. Очереди / воркеры / кэш / БД

| Компонент | Нужен? | Заметка |
|---|---|---|
| SQLite / Postgres | **Да** | Одна БД; Postgres предпочтителен если multi-writer |
| Redis | Опционально | dedup keys, rate limits, live cache |
| Queue (RQ/Celery/Arq) | Опционально на MVP | На старте хватит asyncio workers; очередь — когда нагрузка |
| Object storage | Опционально | raw payloads если большие |
| MCP / browser pool | **Нет** | |

MVP: 3 процесса — `ingest`, `engine`, `publisher` + scheduler settle.

---

## 10. Интерфейсы модулей (зафиксировать сразу)

```python
class EventNormalizer(Protocol):
    def normalize(self, raw: RawEvent) -> Event: ...

class OddsNormalizer(Protocol):
    def normalize(self, raw: RawQuote, event: Event) -> OddsQuote: ...

class FilterPolicy(Protocol):
    def allow(self, snap: FeatureSnapshot) -> FilterResult: ...

class ProbabilityModel(Protocol):
    def predict(self, snap: FeatureSnapshot, market: Market) -> float: ...

class SignalEngine(Protocol):
    def run(self, event_id: str) -> list[Signal]: ...

class MessageRenderer(Protocol):
    def render(self, signal: Signal, style: str) -> str: ...

class Publisher(Protocol):
    def publish(self, text: str, meta: dict) -> PublicationResult: ...

class AITriggerPolicy(Protocol):
    def should_enrich(self, event_id: str, context: dict) -> TriggerDecision: ...
```

Это позволяет менять провайдера API и модель вероятности без переписывания Max delivery / risk.

---

## 11. Конфиги вместо хардкода

Один источник правды:
- `filters.yaml` — пороги sports/modes
- `risk.yaml` — kelly caps / modes
- `delivery.yaml` — `channel_type: max`, dedup hours; tokens via env
- Secrets — только env / secret store (`API_SPORT_RU_KEY`, `MAX_BOT_TOKEN`, `MAX_CHAT_ID`)

Убить drift `system_config.yaml` vs `optimized_filters.py`.

---

## 12. Неочевидные сильные решения старой системы (перенести)

1. Collect-all → filter-later для data science фазы.
2. AI call signature dedup.
3. Phrase bank rotation для канала.
4. Fun_live как отдельный risk mode (продуктово полезно).
5. Failed message dump directory (теперь для Max).
6. WAL + busy_timeout паттерн (если останетесь на SQLite).
