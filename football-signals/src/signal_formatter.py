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
    kind = (signal.signal_kind or "value").lower()

    if kind == "lock":
        reasons = signal.lock_reasons or []
        reason_block = ""
        if reasons:
            reason_block = "Почему верняк:\n" + "\n".join(f"— {r}" for r in reasons[:5]) + "\n"
        conf = (
            f"Уверенность AI: {signal.lock_confidence:.0%}\n"
            if signal.lock_confidence is not None
            else ""
        )
        return (
            f"ВЕРНЯК\n"
            f"Матч: {signal.home_team} — {signal.away_team}\n"
            f"Лига: {signal.league_name}\n"
            f"Дата/время: {signal.kickoff or '—'}\n"
            f"Исход: {signal.outcome_label}\n"
            f"Оценка вероятности (наша модель): {signal.model_prob:.0%}\n"
            f"{conf}"
            f"Букмекер: {bk}, коэффициент {signal.best_odds:.2f}\n"
            f"Линия согласна с фаворитом (это не value-поиск edge).\n"
            f"{reason_block}"
            f"Рекомендованный размер ставки: {signal.stake_fraction:.2%} банка "
            f"({stake_rub:.0f} руб. при банке {bankroll_amount:.0f})"
        )

    return (
        f"VALUE\n"
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
    """
    lines = [
        f"Сводка системы на {target_date.isoformat()}",
        f"Проверено матчей с RU-коэффициентами: {matches_with_odds}",
        f"Из whitelist-лиг (prematch): {matches_in_whitelist}",
    ]
    if not signals:
        lines.append(
            "Сигналов сегодня нет: ни value (P≥80% + edge>0), "
            "ни верняк (префильтр + AI) не прошли."
        )
        lines.append("Ждём следующий прогон — качество важнее частоты.")
    else:
        n_value = sum(1 for s in signals if (s.signal_kind or "value") != "lock")
        n_lock = sum(1 for s in signals if (s.signal_kind or "") == "lock")
        lines.append(
            f"Опубликовано сигналов: {len(signals)} (value={n_value}, верняк={n_lock})"
        )
        for s in signals:
            tag = "ВЕРНЯК" if (s.signal_kind or "") == "lock" else "VALUE"
            lines.append(
                f"— [{tag}] {s.home_team} — {s.away_team}: {s.outcome_label} "
                f"({s.model_prob:.0%}, {s.best_bookmaker}@{s.best_odds:.2f})"
            )
    return "\n".join(lines)
