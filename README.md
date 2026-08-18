# bet-system — «Честная ставка»

Автопрогон футбольных сигналов: API-SPORT → модель → MAX.

Рабочий код только в папке [`football-signals/`](football-signals/).

Расписание GitHub Actions (МСК): старт 08:00 / 13:30 / 19:30 — пост в канале
обычно через ~30 мин (08:30 / 14:00 / 20:00). Workflow  
[`.github/workflows/football-signals.yml`](.github/workflows/football-signals.yml).

Локально:

```bash
cd football-signals
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # заполнить ключи
python scripts/run_daily.py
```

Secrets/Variables — в настройках репозитория GitHub (см. `football-signals/README.md`).
