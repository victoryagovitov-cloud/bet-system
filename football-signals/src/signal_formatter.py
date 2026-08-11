from __future__ import annotations

from datetime import date

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


def format_daily_digest(
    *,
    target_date: date,
    matches_with_odds: int,
    matches_in_whitelist: int,
    signals: list[SignalCandidate],
) -> str:
    """
    Короткая сводка для «живости» канала даже в дни без ставок.
    Не подгоняет сигналы — честно сообщает, что фильтр 80%+edge ничего не нашёл.
    """
    lines = [
        f"Сводка системы на {target_date.isoformat()}",
        f"Проверено матчей с RU-коэффициентами: {matches_with_odds}",
        f"Из whitelist-лиг (prematch): {matches_in_whitelist}",
    ]
    if not signals:
        lines.append(
            "Сигналов на ставку сегодня нет: ни один исход не прошёл "
            "фильтр P≥80% и положительный edge против лучшего из 4 БК."
        )
        lines.append("Ждём следующий прогон — качество важнее частоты.")
    else:
        lines.append(f"Опубликовано сигналов: {len(signals)}")
        for s in signals:
            lines.append(
                f"— {s.home_team} — {s.away_team}: {s.outcome_label} "
                f"({s.model_prob:.0%}, {s.best_bookmaker}@{s.best_odds:.2f})"
            )
    return "\n".join(lines)
