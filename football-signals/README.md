# Football Signals MVP (API-SPORT.ru → Max)

Система ежедневных футбольных сигналов:

1. Тянет prematch-матчи на дату из [API-SPORT.ru](https://docs.api-sport.ru/)
2. Оставляет только матчи с коэффициентами RU-букмекеров: `marathon`, `melbet`, `betboom`, `pari`
3. Фильтрует лиги по `config/leagues_whitelist.yaml`
4. Считает **независимую** вероятность (Пуассон на pregame h2h/streaks)
5. Публикует только исходы с `P ≥ 80%` и **положительным edge** против лучшего из 4 коэффициентов
6. Считает ставку: `min(¼ Kelly, 1/30 банка)`
7. Пишет сигнал в MAX (или dry-run файл) + SQLite

## Быстрый старт

```bash
cd football-signals
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# впишите API_SPORT_KEY (и позже MAX_*)
python scripts/run_daily.py --date 2026-08-12
```

По умолчанию `PUBLISH_MODE=dry_run` — сигналы сохраняются в `data/signals_dry_run/`.

## MAX (когда будете готовы)

1. Создайте бота в MAX, получите токен
2. Добавьте бота админом канала
3. Узнайте `chat_id` через Bot API (`/updates` или subscriptions)
4. В `.env`:
   - `MAX_BOT_TOKEN=...`
   - `MAX_CHANNEL_CHAT_ID=...`
   - `PUBLISH_MODE=live`
5. Установите `maxapi` (`pip install maxapi`)

## Важные решения

- Коэффициент ≠ вероятность: модель не читает `oddsBk` на вход
- Edge ≤ 0 → сигнал не публикуется даже при P≥80%
- Потолок ставки 1/30 — жёсткий cap поверх ¼ Kelly
- На 2026-08-12 топ-лиг мало (межсезонье/кубки) — whitelist уже содержит Big-5 + РПЛ + еврокубки; сигналов может быть 0, это нормально

## Тесты

```bash
pytest -q
```

## Связь с аудитом

Логика согласована с `../AUDIT_REWRITE/` (API-Sport primary, Max delivery, football prematch only).
