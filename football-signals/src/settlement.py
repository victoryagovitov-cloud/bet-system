from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from config.settings import Settings
from src.api_sport_client import ApiSportClient, ApiSportError
from src.db.repository import SignalRepository
from src.metrics import calibration_report, compute_clv
from src.value_engine import best_odds_across_bookmakers

ROOT = Path(__file__).resolve().parents[1]


def _score_tuple(match: dict) -> tuple[int | None, int | None, str | None]:
    hs = match.get("homeScore") or {}
    as_ = match.get("awayScore") or {}
    home = hs.get("current")
    away = as_.get("current")
    if home is None:
        home = hs.get("display")
    if away is None:
        away = as_.get("display")
    try:
        home_i = int(home) if home is not None else None
        away_i = int(away) if away is not None else None
    except (TypeError, ValueError):
        return None, None, None
    if home_i is None or away_i is None:
        return None, None, None
    return home_i, away_i, f"{home_i}:{away_i}"


def grade_outcome(outcome: str, home: int, away: int) -> bool | None:
    """True/False = win/loss; None = void (DNB push) or unknown market."""
    if outcome == "w1":
        return home > away
    if outcome == "x":
        return home == away
    if outcome == "w2":
        return home < away
    if outcome == "dc_1x":
        return home >= away
    if outcome == "dc_x2":
        return home <= away
    if outcome == "dc_12":
        return home != away
    if outcome == "btts_yes":
        return home > 0 and away > 0
    if outcome == "btts_no":
        return home == 0 or away == 0
    if outcome == "total_over_25":
        return (home + away) > 2.5
    if outcome == "total_under_25":
        return (home + away) < 2.5
    if outcome == "dnb_1":
        if home == away:
            return None
        return home > away
    if outcome == "dnb_2":
        if home == away:
            return None
        return away > home
    return None


@dataclass
class SettleSnapshot:
    settled_now: int
    pending: int
    n: int
    hit_rate: float | None
    mean_model_prob: float | None
    brier: float | None
    mean_clv: float | None
    by_league: dict
    voids_now: int = 0

    def to_dict(self) -> dict:
        return {
            "settled_now": self.settled_now,
            "voids_now": self.voids_now,
            "pending": self.pending,
            "n": self.n,
            "hit_rate": self.hit_rate,
            "mean_model_prob": self.mean_model_prob,
            "brier": self.brier,
            "mean_clv": self.mean_clv,
            "by_league": {str(k): v for k, v in self.by_league.items()},
        }


def settle_pending(settings: Settings) -> SettleSnapshot:
    """Grade finished published signals; write calibration_latest.json."""
    repo = SignalRepository(settings.database_url)
    rows = repo.unsettled()
    settled = 0
    voids = 0

    with ApiSportClient(
        settings.api_sport_base_url,
        settings.api_sport_key,
        settings.api_sport_sport_slug,
    ) as client:
        for row in rows:
            try:
                match = client.get_match_detail(row.match_id, settings.bookmakers_whitelist)
            except ApiSportError as exc:
                logger.warning("cannot fetch match {}: {}", row.match_id, exc)
                continue

            closing_bk, closing_odds = best_odds_across_bookmakers(
                match.get("oddsBk") or {},
                settings.bookmakers_whitelist,
                row.outcome,
            )
            clv = None
            if closing_odds is not None:
                clv = compute_clv(float(row.best_odds), float(closing_odds))

            if match.get("status") != "finished":
                continue

            home, away, score = _score_tuple(match)
            if home is None or away is None:
                continue
            won = grade_outcome(row.outcome, home, away)
            if won is None and row.outcome not in {"dnb_1", "dnb_2"}:
                logger.warning(
                    "cannot grade outcome={} match={} score={}",
                    row.outcome,
                    row.match_id,
                    score,
                )
                continue
            grade = "VOID" if won is None else ("WIN" if won else "LOSS")
            final = score if won is not None else f"{score} void"
            repo.mark_settled(
                row.id,
                won,
                final,
                closing_odds=closing_odds,
                closing_bookmaker=closing_bk,
                clv=clv,
            )
            settled += 1
            if won is None:
                voids += 1
            logger.info(
                "settled #{} {} -> {} clv={}",
                row.id,
                final,
                grade,
                None if clv is None else round(clv, 4),
            )

    report = calibration_report(repo.settled_published())
    pending = len(repo.unsettled())
    snap = SettleSnapshot(
        settled_now=settled,
        voids_now=voids,
        pending=pending,
        n=report.n,
        hit_rate=report.hit_rate,
        mean_model_prob=report.mean_model_prob,
        brier=report.brier,
        mean_clv=report.mean_clv,
        by_league=report.by_league,
    )
    out = ROOT / "data" / "calibration_latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if report.n >= 20 and report.mean_model_prob and report.hit_rate is not None:
        gap = report.mean_model_prob - report.hit_rate
        if gap > 0.10:
            logger.warning(
                "calibration gap: model mean {:.0%} vs hit-rate {:.0%} — model may be overconfident",
                report.mean_model_prob,
                report.hit_rate,
            )
    return snap
