# Football Signals MVP (API-SPORT.ru → Max)

Система футбольных сигналов:

1. Prematch из [API-SPORT.ru](https://docs.api-sport.ru/) только с RU-БК (`marathon/melbet/betboom/pari`)
2. Whitelist лиг → независимая вероятность (Пуассон на pregame)
3. **VALUE:** публикация при `P_model ≥ 80%` **и** `edge = P_model − 1/odds > 0`
4. **ВЕРНЯК:** мягкий префильтр + обязательный AI по данным API (кэф сам по себе не критерий); edge может быть ≈0
5. На матч — не больше одного сигнала (value приоритетнее)
6. Ставка value: `min(¼ Kelly, 1/30 банка)`; верняк: фикс `1/60` банка
7. Дедуп по `(match_id, outcome)` — повторно не публикуем
8. Опциональный LLM-gate для value: новости (Perplexity) + логика; для верняка AI обязателен (fail-closed)
9. MAX или dry-run + SQLite (+ Brier/CLV/статистика по лигам)

Таргет канала: **0–5 сигналов/день** (живость + качество). Частоту регулируем whitelist’ом, спектром рынков и гигиеной value:
- `MIN_EDGE`…`MAX_EDGE` (по умолчанию 2%…15%) — слишком жирный edge = недоверие к модели;
- не публикуем VALUE, если исход **спорит с фаворитом рынка** (1X2 / тотал / ОЗ);
- не больше `MAX_VALUE_SIGNALS_PER_RUN` (по умолчанию 5) value за прогон;
- LLM logic — **стоп-кран** (скептик): те же правила + контекст 1X2 и сила сезона; `ok=false` всегда блок, fail-open только при сбое шлюза;
- «верняк» — явный фаворит «на голову выше» (таблица/сезон/λ), не «безоговорочная гарантия» и не «просто неплохо смотрится».

Модель: сила сезона из таблицы API (`scoresFor`/`scoresAgainst`) → λ атаки/защиты, плюс лёгкие поправки h2h/form/streaks. Без кэфов БК в вероятности.

В межсезонье топ-5 Европы (до ~21–28 августа) в whitelist добавлены «летние» лиги: MLS, Liga MX, Eliteserien, Allsvenskan, J-League 1, K-League 1.

Рынки на матч (подписи как в RU-БК): П1/X/П2, 1X/12/X2, ОЗ — да/нет, ТБ/ТМ 2.5, Фора 1 (0) / Фора 2 (0) — каждый со своим edge.

Даже при 0 сигналах публикуется короткая **ежедневная сводка** (сколько матчей проверено, почему ставок нет).

## Быстрый старт

```bash
cd football-signals
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/run_daily.py --date 2026-08-15
python scripts/track_results.py
```

## Edge: почему 80% модели при implied 83–85% у БК — это ОТСЕВ

Если `1/odds > P_model`, вы платите дороже своей оценки. Высокая вероятность ≠ value. Правило `edge > 0` не смягчаем.

## Дедуп и опросы

Уникальный ключ `(match_id, outcome)`. Повторный прогон не публикует снова; если коэффициент лучшего БК вырос — только логируем улучшение (без репоста на MVP).

Рекомендуемый ритм: 2–3 раза/день (утро / день / вечер) — см. GitHub Actions.

## LLM quality gate (опционально)

В `.env`:

```text
LLM_QUALITY_ENABLED=true
NEWS_LLM_ENABLED=true
NEWS_LLM_API_KEY=...          # Perplexity
NEWS_LLM_BASE_URL=https://api.perplexity.ai
NEWS_LLM_MODEL=sonar

LOGIC_LLM_ENABLED=true
LOGIC_LLM_API_KEY=...         # AITunnel / OpenRouter (дешёвая модель)
LOGIC_LLM_BASE_URL=https://api.aitunnel.ru/v1
LOGIC_LLM_MODEL=deepseek-chat

# Верняки (AI обязателен; без ключа не публикуются)
LOCK_SIGNALS_ENABLED=true
LOCK_LLM_API_KEY=...          # по умолчанию = LOGIC_LLM_API_KEY
```

Количественная модель остаётся Python/Пуассон. LLM только на коротком списке кандидатов:  
NEWS → Perplexity Sonar; LOGIC → дешёвая модель; LOCK → тот же LOGIC-клиент (или `LOCK_LLM_*`).

## GitHub Actions

Workflow: `.github/workflows/football-signals.yml`  
Secrets: `API_SPORT_KEY`, `MAX_BOT_TOKEN`, `MAX_CHANNEL_CHAT_ID`, опционально `NEWS_LLM_API_KEY`, `LOGIC_LLM_API_KEY`, `BANKROLL_AMOUNT`.  
Vars: `PUBLISH_MODE`, `LLM_QUALITY_ENABLED`, `NEWS_LLM_ENABLED`, `LOGIC_LLM_ENABLED`.

После прогона `data/signals.db` коммитится обратно в репозиторий (простое состояние между эфемерными runners).

## Метрики

`track_results.py` после каждого GitHub Actions прогона (08/14/20 МСК) автоматически:
- подтягивает финальный счёт из API;
- ставит WIN / LOSS / VOID (фора 0 при ничьей);
- считает hit-rate, **Brier**, средний **CLV**, ROI по лигам;
- пишет снимок в `data/calibration_latest.json`;
- публикует в MAX мини-отчёт **УЧЁТ РЕЗУЛЬТАТОВ** (`--publish`).

Вручную: `python scripts/track_results.py --publish`.

Чеклист раз в 3 дня: [`docs/CHECKLIST_3DAYS.md`](docs/CHECKLIST_3DAYS.md).

Аномальный разброс коэффициентов между 4 БК логируется (`ODDS_SPREAD_ANOMALY_THRESHOLD`).

## Тесты

```bash
pytest -q
```
