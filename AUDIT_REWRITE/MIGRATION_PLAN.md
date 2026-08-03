# MIGRATION_PLAN — «Что берем» + план перехода

**Дата:** 2026-08-03 (обновлено: Max + API-Sport; autostart frozen)

---

## Решения, уже закрытые

| Вопрос | Решение |
|---|---|
| Primary odds/events API | **API-Sport.ru** → `API_SPORT_CONTRACT.md` |
| Канал доставки | **Max Messenger** (не Telegram) |
| Legacy autostart | Отключён |
| MVP scope | **football + prematch + known/top leagues only** |
| Live / handball / multi-sport | Вне MVP (отложено) |

---

## Документ A. Что берем в новую систему

### Берем без изменений (или почти)
| Артефакт | Путь |
|---|---|
| Kelly fraction math | `src/risk/kelly.py` |
| Phrase banks | `improve_telegram_messages.py` → JSON (контент тот же для Max) |
| Канон структуры сигналов | `MESSAGE_TEMPLATE_STANDARD.md` / `TELEGRAM_STRUCTURE.md` |
| Risk mode numbers | `config/strategy.json`, `config/risk_limits.json` |
| Match ID normalize helpers | `src/tracking/match_id_generator.py` (fallback only) |
| Team aliases seed | `src/matching/team_aliases.json` |
| EV/edge formulas | signal_generator / hybrid_bet_decider |
| Handball totals calculator | `src/handball/totals_calculator.py` — **на полку** (нет handball в API-Sport) |
| API-Sport legacy adapters | как референс запросов: `src/data/api_sport_adapter.py` (без копирования ключей) |

### Берем, но рефакторим
| Артефакт | Как |
|---|---|
| Live football filters | YAML + pure functions |
| AI triggers policy | отвязать от predictions_db |
| Signal generator | EV+gates; без JSON-scrape glue |
| TelegramPublisher | → `delivery/max/renderer` + `publisher` |
| Structured AI client | Pydantic/schema approach |
| Line movement | OddsQuote time series из oddsBk |
| Adaptive thresholds | evaluation job |

### Переписываем с нуля
| Область | Почему |
|---|---|
| Ingest | ApiSportProvider + normalize |
| DB schema | одна модель; Match.id primary |
| Workers / scheduler | вместо 40 bat |
| `generate_live_report.py` | монолит |
| Max Bot client | новый транспорт |
| Dashboards | тонкий health |

### Удаляем
- MCP/browser, HTML collectors, autocorrector, AI Prime parsing
- AHK / prevent_windows_updates
- Dual DB как две правды
- Telegram hot path (оставить только архив шаблонов)

### Требует ручной проверки
| Вопрос | Зачем |
|---|---|
| Max Bot API docs / токены | реализация publisher |
| Exact `OddsChoice` JSON + stats keys (xG/SoT/poss) | FeatureSnapshot mapping |
| Лимиты тарифа API-Sport | poll vs WS |
| AI в MVP или numbers-only? | scope |
| Archive strategy для `predictions.db` | место/бэкап |
| Ротация ключей (API-Sport hardcoded в legacy) | security |

---

## Документ B. План миграции

### Phase 0 — Freeze legacy ✅
- Autostart disabled; MCP stopped; audit docs in `AUDIT_REWRITE/`.

### Phase 1 — Skeleton (2–4 дня)
1. Создать `new_system/` (или новый git repo).
2. Интерфейсы Provider/Normalizer/Engine/Renderer/Publisher.
3. Port domain: Kelly, EV, football filters YAML.
4. Port phrase banks → `delivery/max/phrases/`.

### Phase 2 — API ingest MVP (3–7 дней)
1. `ApiSportProvider`: football, `status=notstarted` (prematch), date/`days_ahead`.
2. Raw store + normalize Event/OddsQuote.
3. REST poll (WS **не** нужен для prematch MVP).
4. League allowlist filter by `tournament.id`.
5. Health: last ingest age, prematch count in allowlist.

### Phase 3 — Signals → Max MVP (3–7 дня)
1. Prematch gates: known leagues + odds band + EV ≥5% + risk caps.
2. Dedup + **Max** publish (shadow file mode сначала).
3. Settlement по `status=finished` для тех же match.id.
4. Сравнить качество 3–5 дней без автопостинга.

### Phase 4 — Hardening
1. Settlement + PnL.
2. Optional AI enricher.
3. WS live.
4. Archive legacy runtime.

### Phase 5 — Product
1. Digest vs single-signal.
2. Multi-sport из доступных slug (tennis/hockey…) по мере готовности фильтров.
3. Admin health + alerts.

---

## Следующие 10 шагов (актуально)

1. Max Bot API credentials + контракт send-message.
2. Снять 1–2 JSON **prematch** football (match + oddsBk) из известных лиг.
3. Зафиксировать `leagues.yaml` allowlist (seed: `TOP_LEAGUE_IDS` из `api_sport_adapter.py`).
4. Создать скелет `new_system/` под **prematch-only**.
5. `ApiSportProvider.list_prematch(sport=football, days_ahead=…)`.
6. Нормализаторы Event/OddsQuote + league gate.
7. Port EV/Kelly + prematch risk modes.
8. `delivery/max/renderer` (компактный prematch EV-шаблон).
9. Shadow publisher (файл/БД).
10. 3–5 дней paper → Max channel.

---

## Критерии готовности MVP

- [ ] Нет HTML/MCP в runtime
- [ ] Ingest только API-Sport **football prematch**
- [ ] Только allowlist известных лиг
- [ ] Сигнал из нормализованных odds + meta
- [ ] Публикация в **Max** (или shadow)
- [ ] Формат = компактный EV + discipline + disclaimer
- [ ] Dedup + risk caps
- [ ] Legacy autostart выключен
- [ ] Unit-тесты EV/Kelly/league gate/normalize
- [ ] Один конфиг порогов + leagues.yaml
- [ ] Нет live/handball кода в MVP path
