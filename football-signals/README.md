# Football Signals MVP (API-SPORT.ru → Max)

Система футбольных сигналов:

1. Prematch из [API-SPORT.ru](https://docs.api-sport.ru/) только с RU-БК (`marathon/melbet/betboom/pari`)
2. Whitelist лиг → независимая вероятность (Пуассон на pregame)
3. Публикация **только** при `P_model ≥ 80%` **и** `edge = P_model − 1/odds > 0`
4. Ставка: `min(¼ Kelly, 1/30 банка)`
5. Дедуп по `(match_id, outcome)` — повторно не публикуем
6. Опциональный LLM-gate: новости (Perplexity) + логика (дешёвая модель)
7. MAX или dry-run + SQLite (+ Brier/CLV/статистика по лигам)

Таргет канала: **0–3 сигнала/день**. Частоту регулируем whitelist’ом, **не** снижением порога 80% и **не** отключением edge>0.

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
LOGIC_LLM_API_KEY=...         # AITunnel / OpenRouter
LOGIC_LLM_BASE_URL=https://api.aitunnel.ru/v1
LOGIC_LLM_MODEL=deepseek-chat
```

Количественная модель остаётся Python/Пуассон. LLM только на коротком списке кандидатов.

## GitHub Actions

Workflow: `.github/workflows/football-signals.yml`  
Secrets: `API_SPORT_KEY`, `MAX_BOT_TOKEN`, `MAX_CHANNEL_CHAT_ID`, опционально `NEWS_LLM_API_KEY`, `LOGIC_LLM_API_KEY`, `BANKROLL_AMOUNT`.  
Vars: `PUBLISH_MODE`, `LLM_QUALITY_ENABLED`, `NEWS_LLM_ENABLED`, `LOGIC_LLM_ENABLED`.

После прогона `data/signals.db` коммитится обратно в репозиторий (простое состояние между эфемерными runners).

## Метрики

`track_results.py` считает hit-rate, **Brier score**, средний **CLV**, ROI/hit-rate **по лигам**. Аномальный разброс коэффициентов между 4 БК логируется (`ODDS_SPREAD_ANOMALY_THRESHOLD`).

## Тесты

```bash
pytest -q
```
