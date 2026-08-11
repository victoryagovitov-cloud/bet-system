from __future__ import annotations

from src.value_engine import SignalCandidate


BOOKMAKER_NAMES = {
    "marathon": "Marathonbet",
    "melbet": "Melbet",
    "betboom": "BetBoom",
    "pari": "Пари",
}


def format_signal(signal: SignalCandidate, bankroll_amount: float) -> str:
    bk = BOOKMAKER_NAMES.get(signal.best_bookmaker, signal.best_bookmaker)
    stake_rub = signal.stake_fraction * bankroll_amount
    return (
        f"Матч: {signal.home_team} — {signal.away_team}\n"
        f"Лига: {signal.league_name}\n"
        f"Дата/время: {signal.kickoff or '—'}\n"
        f"Исход: {signal.outcome_label}\n"
        f"Оценка вероятности (наша модель): {signal.model_prob:.0%}\n"
        f"Букмекер с лучшим коэффициентом: {bk}, коэффициент {signal.best_odds:.2f}\n"
        f"Edge: {signal.edge:.1%}\n"
        f"Рекомендованный размер ставки: {signal.stake_fraction:.2%} банка "
        f"({stake_rub:.0f} руб. при банке {bankroll_amount:.0f})"
    )
