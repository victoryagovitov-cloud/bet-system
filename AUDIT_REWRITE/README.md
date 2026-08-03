# README — Аудит переработки Backtothestart → API-система

**Дата:** 2026-08-03

## Документы

| Файл | Содержание |
|---|---|
| [PROJECT_TREE.md](PROJECT_TREE.md) | Дерево, категории файлов, дубли, опасные места |
| [SYSTEM_ANALYSIS.md](SYSTEM_ANALYSIS.md) | Как работала старая система end-to-end |
| [TELEGRAM_STRUCTURE.md](TELEGRAM_STRUCTURE.md) | Формат сигналов (контент) → доставка в Max |
| [REUSABLE_LOGIC.md](REUSABLE_LOGIC.md) | Фильтры, EV, Kelly, handball, dedup |
| [AUTOSTART_AUDIT.md](AUTOSTART_AUDIT.md) | Автозапуски: найдено / отключено |
| [API_SPORT_CONTRACT.md](API_SPORT_CONTRACT.md) | Primary API: auth, Match, oddsBk, WS |
| [NEW_ARCHITECTURE_DRAFT.md](NEW_ARCHITECTURE_DRAFT.md) | API-Sport ingest + Max delivery |
| [MIGRATION_PLAN.md](MIGRATION_PLAN.md) | Что берем / удаляем + фазы миграции |

**Закрытые решения:** primary API = API-Sport.ru; messaging = Max; MVP = **football prematch, known/top leagues only** (no live, no handball).

## Автозапуск — backup

`_autostart_backup/20260803_233254/` — перемещённый Startup shortcut + export задачи + инструкции отката.

`DISABLE_AI_PRIME_CRON_AS_ADMIN.ps1` — отключение Task Scheduler от администратора.
