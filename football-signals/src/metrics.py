from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from src.db.models import SignalRow


@dataclass
class CalibrationReport:
    n: int
    hit_rate: float | None
    mean_model_prob: float | None
    brier: float | None
    mean_clv: float | None
    by_league: dict[int, dict]


def brier_score(rows: list[SignalRow]) -> float | None:
    """Brier = mean( (p - y)^2 ), y in {0,1}."""
    scored = [r for r in rows if r.result_win is not None and r.model_prob is not None]
    if not scored:
        return None
    total = 0.0
    for r in scored:
        y = 1.0 if r.result_win else 0.0
        total += (float(r.model_prob) - y) ** 2
    return total / len(scored)


def compute_clv(publish_odds: float, closing_odds: float) -> float:
    """
    CLV в вероятностных пунктах: implied_close - implied_publish.
    >0 значит взяли цену лучше закрывающей линии (выгоднее рынка на закрытии).
    """
    if publish_odds <= 1.0 or closing_odds <= 1.0:
        return 0.0
    return (1.0 / closing_odds) - (1.0 / publish_odds)


def calibration_report(rows: list[SignalRow]) -> CalibrationReport:
    settled = [r for r in rows if r.result_win is not None]
    n = len(settled)
    if n == 0:
        return CalibrationReport(0, None, None, None, None, {})

    hits = sum(1 for r in settled if r.result_win)
    hit_rate = hits / n
    mean_p = sum(float(r.model_prob) for r in settled) / n
    brier = brier_score(settled)
    clvs = [float(r.clv) for r in settled if r.clv is not None]
    mean_clv = (sum(clvs) / len(clvs)) if clvs else None

    by_league: dict[int, dict] = {}
    buckets: dict[int, list[SignalRow]] = defaultdict(list)
    for r in settled:
        buckets[int(r.league_id)].append(r)
    for lid, group in buckets.items():
        g_hits = sum(1 for r in group if r.result_win)
        g_n = len(group)
        # simple ROI assuming flat stake_fraction * odds - 1 on win, -stake on loss
        pnl = 0.0
        stake_sum = 0.0
        for r in group:
            s = float(r.stake_fraction or 0)
            stake_sum += s
            if r.result_win:
                pnl += s * (float(r.best_odds) - 1.0)
            else:
                pnl -= s
        by_league[lid] = {
            "n": g_n,
            "hit_rate": g_hits / g_n,
            "roi": (pnl / stake_sum) if stake_sum > 0 else None,
            "league_name": group[0].league_name,
            "brier": brier_score(group),
        }

    return CalibrationReport(
        n=n,
        hit_rate=hit_rate,
        mean_model_prob=mean_p,
        brier=brier,
        mean_clv=mean_clv,
        by_league=by_league,
    )
