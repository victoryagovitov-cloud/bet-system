# Continuity Ledger: Football Match Data Collection + ML Strategy System

## Goal

Deep rewrite into an **API-first** TrueLiveBet signal system:
- **Ingest:** API-Sport.ru (REST; WS later if needed) — no bookmaker HTML/MCP
- **Scope MVP:** **football + prematch only** in **known/top leagues** (no live, no handball, no multi-sport)
- **Domain:** EV / Kelly / league filters from legacy (prematch path)
- **Delivery:** **Max Messenger** bot (not Telegram)

## Current State

**Status:** SCOPE LOCKED — football prematch, known leagues, API-Sport → Max

**Done:**
- Full audit pack in `AUDIT_REWRITE/`
- Autostart frozen
- Docs: API-Sport primary + Max delivery + football/prematch/known-leagues scope

**Now:**
- Ready to scaffold `new_system/` for **prematch football** pipeline
- Need: Max Bot credentials; sample API-Sport prematch JSON (match + oddsBk) for known leagues

**Next:**
1. Scaffold `new_system/` — ApiSportProvider (prematch) + domain + delivery/max
2. Port league allowlist + EV/Kelly + phrase banks
3. Shadow-run prematch signals to file, then Max

## Key Decisions

- Primary provider: **API-Sport.ru**
- Primary event id: `Match.id`
- Odds priority: `oddsBk.betboom` → other BK → `oddsBase`
- Delivery: **Max**
- **MVP = football prematch only, known/top leagues** (explicitly NOT live, NOT handball, NOT niche sports)
- Live filters / handball totals / multi-sport = out of MVP (keep as future reference only)
- Parsing/MCP out of runtime scope

## Constraints/Assumptions

- Known leagues = seed from legacy `TOP_LEAGUE_IDS` in `src/data/api_sport_adapter.py` + refine as config YAML
- Prematch cadence: poll by date / days_ahead (not live WS required for MVP)
- Rotate secrets; no hardcoded keys

## Open Questions

- Exact Max Bot send-message API shape
- Final league allowlist (IDs) for v1
- AI enricher in MVP or numbers-only first?
- API-Sport rate limits for chosen tariff

## Important Tool Outcomes

- User confirmed 2026-08-03: football + prematch + known leagues is enough for now
