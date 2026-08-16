#!/usr/bin/env python
"""
Manual in-play scan (dry-run only — never publishes to MAX).

Examples:
  python scripts/run_live_scan.py
  python scripts/run_live_scan.py --max 2 --min-edge 0.05
  python scripts/run_live_scan.py --watch 45
  python scripts/run_live_scan.py --all-leagues --reset-session
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from loguru import logger

from config.settings import get_settings, load_leagues_whitelist
from src.api_sport_client import ApiSportClient, ApiSportError
from src.live.discovery import collect_inplay_for_dates
from src.live.live_value import LiveCandidate, evaluate_match
from src.live.session import LiveSession
from src.season_strength import attach_season_stats, index_standings


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Manual live football scan (no channel publish)")
    p.add_argument("--max", type=int, default=2, help="Max live signals for the evening session")
    p.add_argument("--min-edge", type=float, default=0.05, help="Minimum model edge")
    p.add_argument("--max-edge", type=float, default=0.20, help="Maximum model edge (sanity)")
    p.add_argument("--min-prob", type=float, default=0.55, help="Minimum model probability")
    p.add_argument("--min-minute", type=int, default=20, help="Earliest minute window")
    p.add_argument("--max-minute", type=int, default=80, help="Latest minute window")
    p.add_argument(
        "--all-leagues",
        action="store_true",
        help="Do not restrict to leagues whitelist",
    )
    p.add_argument(
        "--allow-no-heuristic",
        action="store_true",
        help="Allow candidates without pressure/tempo heuristic tags",
    )
    p.add_argument(
        "--watch",
        type=int,
        default=0,
        metavar="SECONDS",
        help="Re-scan every N seconds until Ctrl+C (0 = once)",
    )
    p.add_argument(
        "--days",
        type=int,
        default=1,
        help="How many calendar days to pull match lists for (default 1=today)",
    )
    p.add_argument(
        "--json-out",
        type=Path,
        default=ROOT / "data" / "_live_scan_latest.json",
        help="Where to write the last scan JSON",
    )
    p.add_argument(
        "--reset-session",
        action="store_true",
        help="Clear tonight's live session dedup/cap file before scanning",
    )
    p.add_argument(
        "--no-session",
        action="store_true",
        help="Do not persist evening session (print all top candidates up to --max)",
    )
    return p.parse_args(argv)


def _candidate_row(c: LiveCandidate) -> dict:
    return {
        "match_id": c.match_id,
        "minute": c.minute,
        "score": c.score,
        "home": c.home_team,
        "away": c.away_team,
        "league": c.league_name,
        "outcome": c.outcome,
        "label": c.outcome_label,
        "p": round(c.model_prob, 4),
        "bk": c.best_bookmaker,
        "odds": c.best_odds,
        "edge": round(c.edge, 4),
        "lambda_remain": [round(c.lambda_home_remain, 3), round(c.lambda_away_remain, 3)],
        "tempo": [round(c.tempo_home, 3), round(c.tempo_away, 3)],
        "reasons": c.reasons,
        "kind": c.signal_kind,
    }


def _print_candidate(c: LiveCandidate) -> None:
    print(
        f"  LIVE {c.minute}' {c.home_team} {c.score} {c.away_team} | {c.league_name}\n"
        f"       → {c.outcome_label} p={c.model_prob:.0%} @{c.best_odds} "
        f"({c.best_bookmaker}) edge={c.edge:.1%}\n"
        f"       λ_rem={c.lambda_home_remain:.2f}/{c.lambda_away_remain:.2f} "
        f"tempo={c.tempo_home:.2f}/{c.tempo_away:.2f} "
        f"reasons={', '.join(c.reasons) or '—'}",
        flush=True,
    )


def run_once(args: argparse.Namespace, session: LiveSession | None) -> dict:
    get_settings.cache_clear()
    load_leagues_whitelist.cache_clear()
    settings = get_settings()
    if not settings.api_sport_key:
        raise SystemExit("API_SPORT_KEY is empty — set it in .env or the environment")

    bookmakers = settings.bookmakers_whitelist
    standings_cache: dict[int, dict] = {}
    skip_counts: dict[str, int] = {}
    raw_candidates: list[LiveCandidate] = []
    scanned = 0

    with ApiSportClient(
        settings.api_sport_base_url,
        settings.api_sport_key,
        settings.api_sport_sport_slug,
    ) as client:

        def season_for(tid: int | None) -> dict:
            if not tid:
                return {}
            tid_i = int(tid)
            if tid_i not in standings_cache:
                try:
                    standings_cache[tid_i] = client.get_tournament_standings(tid_i)
                except ApiSportError:
                    standings_cache[tid_i] = {}
            return index_standings(standings_cache.get(tid_i) or {})

        def get_matches(d: date) -> list[dict]:
            return client.get_matches(d, bookmakers)

        inplay = collect_inplay_for_dates(
            get_matches,
            days=args.days,
            whitelist_only=not args.all_leagues,
        )
        print(
            f"in-play listed={len(inplay)} whitelist_only={not args.all_leagues}",
            flush=True,
        )

        for brief in inplay:
            mid = brief.get("id")
            try:
                mid_i = int(mid)
            except (TypeError, ValueError):
                continue
            if session is not None and session.already_seen(mid_i):
                skip_counts["session_seen"] = skip_counts.get("session_seen", 0) + 1
                continue
            try:
                detail = client.get_match_detail(mid_i, bookmakers)
            except ApiSportError as exc:
                logger.warning("match {} detail failed: {}", mid_i, exc)
                skip_counts["detail_error"] = skip_counts.get("detail_error", 0) + 1
                continue

            tid = (detail.get("tournament") or {}).get("id") or (
                (brief.get("tournament") or {}).get("id")
            )
            attach_season_stats(detail, season_for(tid))
            scanned += 1
            cand, reason = evaluate_match(
                detail,
                bookmakers,
                min_model_probability=args.min_prob,
                min_edge=args.min_edge,
                max_edge=args.max_edge,
                min_minute=args.min_minute,
                max_minute=args.max_minute,
                require_heuristic=not args.allow_no_heuristic,
            )
            if cand is None:
                key = reason or "unknown"
                skip_counts[key] = skip_counts.get(key, 0) + 1
                continue
            raw_candidates.append(cand)

    raw_candidates.sort(key=lambda c: c.edge, reverse=True)
    if session is not None:
        selected = session.select(raw_candidates)
    else:
        selected = raw_candidates[: max(1, args.max)]

    print(f"scanned_details={scanned} raw_hits={len(raw_candidates)} selected={len(selected)}")
    if skip_counts:
        top_skips = sorted(skip_counts.items(), key=lambda kv: -kv[1])[:8]
        print("skips: " + ", ".join(f"{k}={v}" for k, v in top_skips), flush=True)

    if not selected:
        print("No live candidates this pass.", flush=True)
    else:
        print("Selected (dry-run, not published):", flush=True)
        for c in selected:
            _print_candidate(c)

    payload = {
        "day": date.today().isoformat(),
        "scanned": scanned,
        "listed_inplay": len(inplay),
        "raw_candidates": [_candidate_row(c) for c in raw_candidates],
        "selected": [_candidate_row(c) for c in selected],
        "skips": skip_counts,
        "publish": False,
        "note": "manual dry-run only — channel publish is intentionally disabled",
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {args.json_out}", flush=True)
    return payload


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level="WARNING")

    session: LiveSession | None
    if args.no_session:
        session = None
    else:
        session = LiveSession(max_signals=args.max)
        if args.reset_session:
            session.reset()
            session = LiveSession(max_signals=args.max)
            print("live session reset", flush=True)

    if args.watch and args.watch > 0:
        print(f"watch mode every {args.watch}s (Ctrl+C to stop)", flush=True)
        try:
            while True:
                run_once(args, session)
                if session is not None and session.remaining_slots <= 0:
                    print("evening live cap reached — stopping watch", flush=True)
                    break
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\nstopped", flush=True)
        return 0

    run_once(args, session)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
