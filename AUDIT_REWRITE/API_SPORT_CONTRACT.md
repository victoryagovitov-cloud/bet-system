# API_SPORT_CONTRACT — Primary data provider

**Дата фиксации:** 2026-08-03  
**Docs:** https://docs.api-sport.ru/ · https://docs.api-sport.ru/overview  
**Base URL:** `https://api.api-sport.ru`  
**WS:** `wss://ws.api.api-sport.ru?apiKey=YOUR_API_KEY`

Статус: **PRIMARY** odds+events+stats provider для `new_system/`.

---

## Auth

| Канал | Как |
|---|---|
| REST | Header `Authorization: YOUR_API_KEY` (**без** `Bearer` / `Token`) |
| WebSocket | Query `?apiKey=YOUR_API_KEY` |

Env: `API_SPORT_RU_KEY` (уже встречается в legacy `.env` / adapters).

⚠️ В legacy коде (`src/data/api_sport_adapter.py`) ключ бывает захардкожен — **ротировать** и никогда не коммитить в `new_system/`.

---

## Спорты (sportSlug)

Официально в v2:
`football` · `ice-hockey` · `basketball` · `tennis` · `table-tennis` · `volleyball` · `esports`

**MVP (закрыто):** используем только **`football`**, только **prematch** (`status=notstarted` / ещё не live), только **known/top leagues** (allowlist `tournament.id`).

Handball отсутствует в API — и **не планируется** в текущем MVP.  
Live / WS / multi-sport — отложены.

---

## Ключевые эндпоинты

Паттерн: `/v2/{sportSlug}/...`

| Назначение | Пример |
|---|---|
| Список матчей | `GET /v2/football/matches?status=inprogress&with_bk_odds=true` |
| Детали матча | `GET /v2/football/matches/{matchId}` |
| Prematch по дате | `GET /v2/football/matches?date=YYYY-MM-DD&exclude_amateur=true` |
| Finished | `GET /v2/football/matches?status=finished&...` |
| Поиск | `/v2/{sportSlug}/search` / param `q` |
| Live stream | WS subscribe `sport:{slug}` / `match:{slug}:{id}` → `match_snapshot` / `match_delta` |

Параметры, важные для нас:
- `with_bk_odds=true` → заполняет `oddsBk`
- `with_statistics=true` (если поддерживается в query списка/деталей — проверить в API Reference Try It Out)
- `exclude_amateur=true` — опционально на этапе анализа, не обязательно на raw ingest

---

## Match = первичная сущность

| Поле API | Наш смысл |
|---|---|
| `id` (int) | `provider_event_id` (primary) |
| `status` | `notstarted` / `inprogress` / `finished` / canceled/postponed/... → map to pre/live/finished |
| `statusDescription` | UI/debug |
| `dateEvent`, `startTimestamp` | kickoff (ms → UTC) |
| `currentMatchMinute`, `currentMatchSecond` | минута для фильтров |
| `tournament`, `category`, `season` | Competition context + RU `translations` |
| `homeTeam`, `awayTeam` | Team ids + `name` / `translations.ru` |
| `homeScore`, `awayScore` (+ periods, `display`) | ScoreState |
| `liveEvents[]` | goal/card/sub/period → AI triggers |
| `matchStatistics[]` | FeatureSnapshot (SoT, possession, xG keys via stats dictionary) |
| `oddsBase[]` | базовые рынки |
| `hasBkOdds` + `oddsBk` | котировки Melbet / Pari / Marathon / **BetBoom** |

Старый human `match_id` (`league_home_away_YYYYMMDD`) — **только fallback**, не primary key.

---

## Odds → OddsQuote

```python
@dataclass
class OddsQuote:
    provider: str                 # "api_sport"
    match_id: int                 # Match.id
    bookmaker: str | None         # None for oddsBase; 'betboom'|'pari'|...
    market_name: str              # из OddsMarket.name
    group: str | None
    period: str | None            # ALL / 1ST / ...
    selection: str                # из choice (home/away/draw/over/under/...)
    line: float | None            # тотал/гандикап
    odds: float
    is_live: bool
    suspended: bool
    received_at_utc: datetime     # наш ingest ts
    source: str                   # "oddsBase" | "oddsBk"
```

Приоритет для TrueLiveBet-сигналов (как раньше бренд на BetBoom):
1. `oddsBk.betboom` если есть
2. иначе `oddsBk.pari` / `melbet` / `marathon`
3. иначе `oddsBase`

EV / Kelly / edge формулы **без изменений** (`REUSABLE_LOGIC.md`).

---

## Stats → FeatureSnapshot

Источник: `matchStatistics` (группы по периодам `ALL`, `1ST`, …) + словарь ключей:  
https://docs.api-sport.ru/concepts/statistics-dictionary

Нужно проверить наличие (по футболу) ключей под legacy-фильтры:
- xG / expected goals
- shots on target / shots total
- possession

Если xG нет в тарифе/спорте — dominance-формулу адаптировать на доступные ключи (не парсить HTML).

`liveEvents.type`: `goal` | `card` | `substitution` | `period` | … → триггеры AI.

---

## Provider contract (реализация)

```python
class ApiSportProvider(OddsEventsProvider):
    """Primary provider. Docs: docs.api-sport.ru"""

    def list_live_events(self, sports: list[str]) -> list[RawEvent]:
        # GET /v2/{sport}/matches?status=inprogress&with_bk_odds=true
        ...

    def get_match(self, sport: str, match_id: int) -> RawEvent:
        # GET /v2/{sport}/matches/{match_id}?with_bk_odds=true
        ...

    def iter_odds(self, raw_match: RawEvent) -> list[RawQuote]:
        # flatten oddsBase + oddsBk.*
        ...

    def get_event_stats(self, raw_match: RawEvent) -> RawStats:
        # matchStatistics + liveEvents + clock
        ...

    def get_results(self, sport: str, since: datetime) -> list[RawResult]:
        # status=finished (+ date range params per docs)
        ...

    def subscribe_live(self, sports: list[str]):
        # optional WS: match_snapshot / match_delta
        ...
```

Файлы в новой системе:
- `new_system/ingest/providers/api_sport.py`
- `new_system/normalize/events.py`
- `new_system/normalize/markets.py`

Legacy референс (не копировать secrets):
- `src/data/api_sport_adapter.py`
- `src/data/hybrid_match_provider.py`
- `backtest/backtest_*.py`

---

## Ingest рекомендации

| Режим | Когда |
|---|---|
| REST poll по `date` / `days_ahead`, `status=notstarted` | **MVP (prematch)** |
| WebSocket | не нужен для текущего MVP |
| Append raw payload всегда | replay / debug |

Фильтр лиг: после normalize — allowlist `tournament.id` из `configs/leagues.yaml` (seed: legacy `TOP_LEAGUE_IDS`).

Всегда писать `received_at_utc` отдельно от `startTimestamp` матча.

---

## Open checks (ручная проверка в личном кабинете / Try It Out)

1. Есть ли query `with_statistics` на list vs только detail?
2. Какие exact keys в `matchStatistics` для football live (xg / shots_on_goal / ball_possession)?
3. Структура одного `OddsChoice` (поля line/odds/name) — снять пример JSON.
4. Лимиты тарифа (req/min, WS connections).
5. Появится ли handball в roadmap API — иначе отдельный источник позже.
