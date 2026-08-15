#!/usr/bin/env python
"""Scan API-SPORT for value + lock candidates without publishing."""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.settings import get_settings, load_leagues_whitelist
from src.api_sport_client import ApiSportClient, ApiSportError
from src.league_filter import is_league_allowed
from src import probability_model, value_engine


def main() -> int:
    get_settings.cache_clear()
    settings = get_settings()
    bookmakers = settings.bookmakers_whitelist
    load_leagues_whitelist.cache_clear()
    start = date.today()
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    out: list[dict] = []

    with ApiSportClient(
        settings.api_sport_base_url,
        settings.api_sport_key,
        settings.api_sport_sport_slug,
    ) as client:
        for offset in range(days):
            target = start + timedelta(days=offset)
            try:
                matches = client.get_matches(target, bookmakers)
            except ApiSportError as exc:
                print(f"ERR {target}: {exc}", flush=True)
                continue
            allowed = [
                m
                for m in matches
                if is_league_allowed((m.get("tournament") or {}).get("id"))
                and m.get("status") == "notstarted"
            ]
            print(
                f"{target}: matches_odds={len(matches)} whitelist={len(allowed)}",
                flush=True,
            )
            for m in allowed:
                mid = m.get("id")
                try:
                    detail = client.get_match_detail(int(mid), bookmakers)
                except ApiSportError as exc:
                    print(f"  skip {mid}: {exc}", flush=True)
                    continue
                probs = probability_model.compute(detail)
                value = value_engine.find_signal(
                    detail,
                    probs,
                    bookmakers,
                    min_model_probability=settings.min_model_probability,
                    min_edge=settings.min_edge,
                )
                lock = value_engine.find_lock_candidate(
                    detail,
                    probs,
                    bookmakers,
                    min_model_probability=settings.lock_min_model_probability,
                    odds_min=settings.lock_odds_min,
                    odds_max=settings.lock_odds_max,
                    min_lambda_gap=settings.lock_min_lambda_gap,
                    min_h2h_games=settings.lock_min_h2h_games,
                    min_h2h_share=settings.lock_min_h2h_share,
                )
                if not value and not lock:
                    continue
                pregame = detail.get("pregame") or {}
                row = {
                    "date": target.isoformat(),
                    "match_id": mid,
                    "home": value_engine._team_name(detail.get("homeTeam")),
                    "away": value_engine._team_name(detail.get("awayTeam")),
                    "league": (detail.get("tournament") or {}).get("name"),
                    "kickoff": detail.get("dateEvent"),
                    "lambda_home": probs.get("_lambda_home"),
                    "lambda_away": probs.get("_lambda_away"),
                    "h2h": ((pregame.get("h2h") or {}).get("teamDuel")),
                    "streaks": (pregame.get("teamStreaks") or {}).get("general"),
                    "probs": {
                        k: round(float(v), 4)
                        for k, v in probs.items()
                        if not str(k).startswith("_") and isinstance(v, (int, float))
                    },
                    "value": None,
                    "lock": None,
                }
                if value:
                    row["value"] = {
                        "outcome": value.outcome,
                        "label": value.outcome_label,
                        "p": round(value.model_prob, 4),
                        "bk": value.best_bookmaker,
                        "odds": value.best_odds,
                        "edge": round(value.edge, 4),
                        "implied": round(1 / value.best_odds, 4),
                    }
                if lock:
                    row["lock"] = {
                        "outcome": lock.outcome,
                        "label": lock.outcome_label,
                        "p": round(lock.model_prob, 4),
                        "bk": lock.best_bookmaker,
                        "odds": lock.best_odds,
                        "edge": round(lock.edge, 4),
                        "implied": round(1 / lock.best_odds, 4),
                    }
                out.append(row)
                tag = []
                if value:
                    tag.append(
                        f"VALUE {value.outcome_label} p={value.model_prob:.0%} "
                        f"@{value.best_odds} edge={value.edge:.1%}"
                    )
                if lock:
                    tag.append(
                        f"LOCK {lock.outcome_label} p={lock.model_prob:.0%} "
                        f"@{lock.best_odds} edge={lock.edge:.1%}"
                    )
                print(f"  CAND {row['home']} — {row['away']}: " + " | ".join(tag), flush=True)

    path = ROOT / "data" / f"_scan_candidates_{start.isoformat()}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {len(out)} candidates -> {path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
