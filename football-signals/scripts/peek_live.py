#!/usr/bin/env python
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from config.settings import get_settings
from src.api_sport_client import ApiSportClient
from src.league_filter import is_league_allowed
from src import value_engine


def score_str(m: dict) -> str:
    hs = m.get("homeScore")
    aws = m.get("awayScore")
    if isinstance(hs, dict):
        h = hs.get("current") or hs.get("display") or hs.get("period1")
    else:
        h = hs
    if isinstance(aws, dict):
        a = aws.get("current") or aws.get("display") or aws.get("period1")
    else:
        a = aws
    return f"{h}-{a}"


def main() -> int:
    get_settings.cache_clear()
    s = get_settings()
    bookmakers = s.bookmakers_whitelist
    rows = []
    with ApiSportClient(s.api_sport_base_url, s.api_sport_key, s.api_sport_sport_slug) as client:
        for d in (date.today(), date.today() + timedelta(days=1)):
            matches = client.get_matches(d, bookmakers)
            for m in matches:
                st = (m.get("status") or "").lower()
                if st in {"notstarted", "finished", "canceled", "cancelled", "postponed", "abandoned"}:
                    continue
                tid = (m.get("tournament") or {}).get("id")
                wl = is_league_allowed(tid)
                home = value_engine._team_name(m.get("homeTeam"))
                away = value_engine._team_name(m.get("awayTeam"))
                lg = ((m.get("tournament") or {}).get("translations") or {}).get("ru") or (
                    m.get("tournament") or {}
                ).get("name")
                rows.append(
                    {
                        "date": d.isoformat(),
                        "id": m.get("id"),
                        "status": st,
                        "desc": m.get("statusDescription"),
                        "min": m.get("currentMatchMinute"),
                        "home": home,
                        "away": away,
                        "league": lg,
                        "whitelist": wl,
                        "score": score_str(m),
                    }
                )
    wl = [r for r in rows if r["whitelist"]]
    print(f"API-SPORT in-play total={len(rows)} whitelist={len(wl)}")
    target = wl if wl else rows[:25]
    for r in target:
        print(
            f"{r['min'] or '?'}' [{r['status']}] {r['home']} {r['score']} {r['away']} | "
            f"{r['league']} | wl={r['whitelist']}"
        )
    out = ROOT / "data" / "_live_snapshot.json"
    out.write_text(json.dumps({"all": rows, "whitelist": wl}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
