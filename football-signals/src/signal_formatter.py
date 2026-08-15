from __future__ import annotations

from datetime import date

from src.phrase_bank import format_footer, pick_closing, pick_disclaimer, pick_discipline
from src.value_engine import SignalCandidate


BOOKMAKER_NAMES = {
    "marathon": "Marathonbet",
    "melbet": "Melbet",
    "betboom": "BetBoom",
    "pari": "Пари",
}


def _body_value(signal: SignalCandidate, bankroll_amount: float) -> str:
    bk = BOOKMAKER_NAMES.get(signal.best_bookmaker, signal.best_bookmaker)
    stake_rub = signal.stake_fraction * bankroll_amount
    return (
        f"VALUE\n"
        f"────────\n"
        f"Матч: {signal.home_team} — {signal.away_team}\n"
        f"Лига: {signal.league_name}\n"
        f"Дата/время: {signal.kickoff or '—'}\n"
        f"\n"
        f"Исход: {signal.outcome_label}\n"
        f"Кэф: {bk} @ {signal.best_odds:.2f}\n"
        f"Оценка модели: {signal.model_prob:.0%}\n"
        f"Edge: {signal.edge:.1%}\n"
        f"\n"
        f"Ставка: {signal.stake_fraction:.2%} банка "
        f"({stake_rub:.0f} ₽ при банке {bankroll_amount:.0f} ₽)"
    )


def _body_lock(signal: SignalCandidate, bankroll_amount: float) -> str:
    bk = BOOKMAKER_NAMES.get(signal.best_bookmaker, signal.best_bookmaker)
    stake_rub = signal.stake_fraction * bankroll_amount
    reasons = signal.lock_reasons or []
    reason_block = ""
    if reasons:
        reason_block = "Почему верняк:\n" + "\n".join(f"— {r}" for r in reasons[:5]) + "\n\n"
    conf = (
        f"Уверенность AI: {signal.lock_confidence:.0%}\n"
        if signal.lock_confidence is not None
        else ""
    )
    return (
        f"ВЕРНЯК\n"
        f"────────\n"
        f"Матч: {signal.home_team} — {signal.away_team}\n"
        f"Лига: {signal.league_name}\n"
        f"Дата/время: {signal.kickoff or '—'}\n"
        f"\n"
        f"Исход: {signal.outcome_label}\n"
        f"Кэф: {bk} @ {signal.best_odds:.2f}\n"
        f"Оценка модели: {signal.model_prob:.0%}\n"
        f"{conf}"
        f"Линия согласна с фаворитом (это не поиск value/edge).\n"
        f"\n"
        f"{reason_block}"
        f"Ставка: {signal.stake_fraction:.2%} банка "
        f"({stake_rub:.0f} ₽ при банке {bankroll_amount:.0f} ₽)"
    )


def format_signal(signal: SignalCandidate, bankroll_amount: float) -> str:
    kind = (signal.signal_kind or "value").lower()
    body = _body_lock(signal, bankroll_amount) if kind == "lock" else _body_value(
        signal, bankroll_amount
    )
    return f"{body}\n\n────────\n{format_footer()}"


def format_daily_digest(
    *,
    target_date: date,
    matches_with_odds: int,
    matches_in_whitelist: int,
    signals: list[SignalCandidate],
    date_window: list[date] | None = None,
) -> str:
    """
    Короткая сводка для «живости» канала даже в дни без ставок.
    """
    if date_window and len(date_window) > 1:
        head = (
            f"СВОДКА · {date_window[0].isoformat()} … {date_window[-1].isoformat()}"
        )
    else:
        head = f"СВОДКА · {target_date.isoformat()}"
    lines = [
        head,
        "────────",
        f"Матчей с RU-кэфами: {matches_with_odds}",
        f"Whitelist (prematch): {matches_in_whitelist}",
    ]
    if not signals:
        lines.append("")
        lines.append(
            "Сегодня без ставки: по правилам (P≥80% + запас над линией / верняк+AI) "
            "ничего не прошло — это нормально."
        )
        lines.append(
            "Молчать лучше, чем публиковать слабый купон. "
            "Следующий прогон снова проверит календарь."
        )
        lines.append(pick_discipline())
        lines.append(pick_closing())
    else:
        n_value = sum(1 for s in signals if (s.signal_kind or "value") != "lock")
        n_lock = sum(1 for s in signals if (s.signal_kind or "") == "lock")
        lines.append("")
        lines.append(f"Опубликовано: {len(signals)} (value={n_value}, верняк={n_lock})")
        for s in signals:
            tag = "ВЕРНЯК" if (s.signal_kind or "") == "lock" else "VALUE"
            lines.append(
                f"— [{tag}] {s.home_team} — {s.away_team}: {s.outcome_label} "
                f"({s.model_prob:.0%}, {s.best_bookmaker}@{s.best_odds:.2f})"
            )
        lines.append("")
        lines.append(pick_discipline())
        lines.append(pick_closing())

    lines.append("")
    lines.append(f"⚠️ {pick_disclaimer()}")
    return "\n".join(lines)
