# REUSABLE_LOGIC — Полезная «начинка» для API-системы

**Дата:** 2026-08-03  
Только то, что полезно **без HTML-парсинга**.

---

## 1. Формулы (брать как библиотеку)

| Имя | Формула | Источник |
|---|---|---|
| EV % | `(p * odds - 1) * 100` | `signal_generator.py`, publisher |
| Edge | `p - 1/odds` | `hybrid_bet_decider.py` |
| Kelly | `f = (p*b - q)/b`, `b=odds-1`, `q=1-p`; clamp `[0, max_fraction]`; None если edge≤0 | `src/risk/kelly.py` |
| Implied | `1/p` | `implied_odds_calculator.py` |
| Ensemble p | `0.55*perp + 0.45*claude` | `signal_generator.py` / `ensemble_weights.py` |
| Dominance (football) | `ΔxG*3 + ΔSoT*2 + Δshots + Δposs*0.5 + (score_diff*2)*(minute/90)` | `graphql_live_analyzer.py` |
| Handball projected total | `total + (total/minute)*(60-minute)` | `totals_calculator.py` |

---

## 2. Фильтры live football

### Strict / Soft — `match_pre_filters.py`
| Правило | Strict | Soft |
|---|---|---|
| Minute | 20–85 | 15–90 |
| Goal lead | ≥0 и <3 | same |
| xG diff | ≥0.4 | ≥0.3 |
| xG total | ≥0.6 | ≥0.3 |
| Possession leader | ≥55% | ≥50% |
| SoT diff | ≥2 | ≥0 |
| Leader SoT | ≥3 | ≥1 |
| Combined SoT | ≥7 | ≥5 |
| Derby/cup/friendly | exclude | allow |
| League | top/tier1/tier2 | reject only low/amateur |

### SAFE / RISKY / PRIMARY — `optimized_filters.py`
- SAFE: prob 65–90%; dominance early/mid/late 8/7/6; xG diff 0.30; poss 55; SoT/shots diff 2
- RISKY: prob ≥82%; dominance 9/8/7; xG 0.40; poss 58; diffs 3
- PRIMARY: odds info band 1.12–1.30; prob ≥78%; …
- 1-goal lead relax: dominance−1, xG−0.05, poss−2, SoT−1
- `ODDS_CORRECTION_FACTOR = 0.87` (legacy; в новой системе заменить на raw API odds + отдельный latency model)

### League taxonomy — `league_filter.py`
Keyword lists TOP / MID / LOW (liga 3/4, amateur, U19–U21, women, friendly).  
В API-эре лучше маппить на **league_id tiers**, keywords — fallback.

### Adaptive — `adaptive_filter_manager.py` + `adaptive_thresholds.json`
Defaults: xG 0.35, poss 55, SoT diff 2, minute_max 85.  
Tighten if error_rate >30%; loosen if <15%; min 10 preds; interval 24h; lr=0.05.  
**Идея сильная** — переписать на чистый config store + evaluation job.

---

## 3. Handball totals — `src/handball/totals_calculator.py`

Константы:
- game 60 мин; analyze 20–55; recommend from 36
- min total score 20; no draws
- score_diff: <40→≥4, 40–44→≥3, ≥45→≥2
- Over if projected ≥62; Under ≤58; 59–61 skip
- Leader prob: `60 + 6*|diff| + 4*max(0,pace-1) + 0.3*max(0,proj-55) - 0.25*remaining`, clamp 58–94
- Sort: `|diff|*5 + pace*2 + 3 if has_rec`

**Статус:** лучший кандидат на «берем почти без изменений».

---

## 4. Signal / value rules

| Правило | Значение | Где |
|---|---|---|
| Min EV для сигнала | **5%** | `generate_signal(..., min_ev=5.0)` |
| AI consensus side | одинаковый Over/Under | `signal_generator` |
| AI consensus proximity | `\|p1-p2\| ≤ 0.15` | same |
| Line-adj edge | move <−2% → +0.01; >4% → −0.02 | `hybrid_bet_decider` |
| Odds change AI trigger | ≥5% relative | `ai_triggers.py` |
| Sentiment change | ≥10% | same |
| AI min interval | 15 min (кроме goal/red_card) | same |

Стратегии (`config/strategy.json`, код `src/strategies/*`) — прототипы, все `enabled:false`:
- BTTS: xG≥1.2/side, rate 0.6, odds 1.5–2.5, value≥0.06
- xG totals: prematch diff 0.5; live sum 0.8 after min 60
- Comeback: mins 15–70, xG dom 0.3, odds 1.8–3.5, value≥0.08, max 1 entry/match

---

## 5. Risk / staking

`config/risk_limits.json`:
- max match risk 5%
- max daily risk 10%
- max daily drawdown 5%
- max live entries/match 2
- fun_live max 5/cycle

Modes (`config/strategy.json`):
| Mode | odds | min_value | max risk |
|---|---|---|---|
| conservative | 1.5–2.2 | 0.05 | 2% |
| standard | 1.6–2.5 | 0.06 | 3% |
| aggressive | 1.7–3.0 | 0.07 | 5% |
| fun_live | 2.0–5.0 | 0.00 | 0.5% stake / 2% daily |

Hybrid units (`hybrid_bet_decider.py`):
- prematch base 0.5% bank; live 0.375%
- edge gates 5% / 8%
- stake factor 0.5–1.5 × unit by edge × line movement

---

## 6. Dedup / antispam / timing

| Механизм | Правило |
|---|---|
| Telegram match dedup | 4 часа (configurable) |
| Diversity select | ≤2 одного типа при заполнении |
| AI signature MD5 | match_id+phase+trigger+odds+sentiment+score+minute |
| No-matches rotation | alternate templates ~20 мин; escalate after 3 empties |
| Comeback max entries | 1 / match |
| Publication windows | AI Prime cron 9:00–00:00; schedulers 13:00 daily (legacy) |

---

## 7. Match identity

`generate_match_id(league, home, away, date)` → `league_home_away_YYYYMMDD` после normalize.  
Для API: **предпочтительно external `event_id`**, старый алгоритм — fallback / human key.

Team matching: `TeamNameResolver` + `team_aliases.json` + rapidfuzz ≥80%.  
Нужен, пока провайдеры не дают единый ID.

---

## 8. Sorting / ranking heuristics

- Handball: dominance_score
- Football live: комбинации dominance, probability, category buckets (time/lead/xG)
- Diversity: не забивать ленту одним типом сигнала

---

## 9. Odds constraints (исторические)

Встречаются полосы:
- Info/primary: ~1.12–1.35 (низкий кэф фаворита)
- Strategy modes: 1.5–5.0 в зависимости от режима
- Validator collectors: [1.01, 50.0]

В API-системе хранить **raw odds + timestamp + bookmaker**; фильтры — поверх.

---

## 10. Что портировать пакетом `domain/`

Рекомендуемый минимальный набор pure functions:
```
domain/
  identity.py          # match_id normalize (fallback)
  markets.py           # EV, edge, implied
  risk/kelly.py
  risk/limits.py
  filters/football_live.py
  filters/league_tier.py
  sports/handball_totals.py
  sports/football_dominance.py
  signals/consensus.py
  signals/gates.py       # min_ev, odds bands
  triggers/ai_policy.py
```

Всё без I/O, БД, Telegram, HTTP.

---

## 11. Не переносить как есть

- Любые CSS selectors / MCP snapshot parsers
- Autocorrector
- `generate_live_report.py` целиком (только извлечь функции)
- Дублирующие analyzer copies
- Hardcoded secrets / correction factor как «магия правды»
