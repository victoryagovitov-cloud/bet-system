from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from src.phrase_bank import (
    format_footer,
    pick_closing,
    pick_disclaimer,
    pick_discipline,
    pick_education,
)
from src.value_engine import SignalCandidate

if TYPE_CHECKING:
    from src.settlement import SettleSnapshot


BOOKMAKER_NAMES = {
    "marathon": "Marathonbet",
    "melbet": "Melbet",
    "betboom": "BetBoom",
    "pari": "Пари",
}


def _pct(x: float | None) -> str:
    if x is None:
        return "пока нет данных"
    return f"{x:.0%}"


def _body_value(signal: SignalCandidate, bankroll_amount: float) -> str:
    bk = BOOKMAKER_NAMES.get(signal.best_bookmaker, signal.best_bookmaker)
    stake_rub = signal.stake_fraction * bankroll_amount
    return (
        f"СТАВКА (ценный коэффициент)\n"
        f"────────\n"
        f"Матч: {signal.home_team} — {signal.away_team}\n"
        f"Лига: {signal.league_name}\n"
        f"Когда: {signal.kickoff or '—'}\n"
        f"\n"
        f"Что берём: {signal.outcome_label}\n"
        f"Коэффициент: {bk} @ {signal.best_odds:.2f}\n"
        f"Наша оценка шанса: {signal.model_prob:.0%}\n"
        f"Запас над ценой букмекера: {signal.edge:.1%}\n"
        f"\n"
        f"Размер: {signal.stake_fraction:.2%} банка "
        f"(около {stake_rub:.0f} ₽, если банк {bankroll_amount:.0f} ₽)"
    )


def _body_lock(signal: SignalCandidate, bankroll_amount: float) -> str:
    bk = BOOKMAKER_NAMES.get(signal.best_bookmaker, signal.best_bookmaker)
    stake_rub = signal.stake_fraction * bankroll_amount
    reasons = signal.lock_reasons or []
    reason_block = ""
    if reasons:
        reason_block = "Почему это сильный фаворит:\n" + "\n".join(
            f"— {r}" for r in reasons[:5]
        ) + "\n\n"
    conf = (
        f"Уверенность проверки: {signal.lock_confidence:.0%}\n"
        if signal.lock_confidence is not None
        else ""
    )
    return (
        f"ВЕРНЯК (явный фаворит)\n"
        f"────────\n"
        f"Матч: {signal.home_team} — {signal.away_team}\n"
        f"Лига: {signal.league_name}\n"
        f"Когда: {signal.kickoff or '—'}\n"
        f"\n"
        f"Что берём: {signal.outcome_label}\n"
        f"Коэффициент: {bk} @ {signal.best_odds:.2f}\n"
        f"Наша оценка шанса: {signal.model_prob:.0%}\n"
        f"{conf}"
        f"Здесь ищем не «вкусную цену», а команду сильнее соперника на голову.\n"
        f"\n"
        f"{reason_block}"
        f"Размер: {signal.stake_fraction:.2%} банка "
        f"(около {stake_rub:.0f} ₽, если банк {bankroll_amount:.0f} ₽)"
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
    pending_settlement: int | None = None,
) -> str:
    """
    Короткая сводка простым языком — даже в дни без ставок.
    """
    if date_window and len(date_window) > 1:
        dates = f"{date_window[0].isoformat()} — {date_window[-1].isoformat()}"
    else:
        dates = target_date.isoformat()

    parts = [
        f"Коротко по проверке · {dates}",
        "",
        "Проверка прошла нормально.",
        f"Посмотрели матчей с коэффициентами наших букмекеров: {matches_with_odds}.",
        f"Из них в наших лигах до игры: {matches_in_whitelist}.",
    ]
    if pending_settlement is not None:
        parts.append(
            f"Ещё ждём результата по ранее данным сигналам: {pending_settlement}."
        )

    if not signals:
        parts.extend(
            [
                "",
                "Новых ставок сейчас нет.",
                "Мы публикуем только то, что проходит строгие правила. "
                "Сегодня подходящего варианта не нашлось — так бывает, и это нормально.",
                "Лучше помолчать, чем дать слабый купон «для галочки».",
                "Следующая проверка снова пройдёт по календарю.",
                "",
                pick_education(),
                pick_discipline(),
                pick_closing(),
            ]
        )
    else:
        n_value = sum(1 for s in signals if (s.signal_kind or "value") != "lock")
        n_lock = sum(1 for s in signals if (s.signal_kind or "") == "lock")
        parts.extend(
            [
                "",
                f"Сейчас опубликовали сигналов: {len(signals)} "
                f"(ценный коэффициент — {n_value}, верняк — {n_lock}).",
            ]
        )
        for s in signals:
            tag = "верняк" if (s.signal_kind or "") == "lock" else "ценный кэф"
            bk = BOOKMAKER_NAMES.get(s.best_bookmaker, s.best_bookmaker)
            parts.append(
                f"— [{tag}] {s.home_team} — {s.away_team}: {s.outcome_label} "
                f"(шанс ~{s.model_prob:.0%}, {bk} {s.best_odds:.2f})"
            )
        parts.extend(
            [
                "",
                pick_education(),
                pick_discipline(),
                pick_closing(),
            ]
        )

    parts.extend(["", f"⚠️ {pick_disclaimer()}"])
    return "\n".join(parts)


def format_accounting_report(snap: SettleSnapshot) -> str:
    """Отчёт по результатам простым языком."""
    parts = [
        "Как сыграли наши сигналы",
        "",
    ]
    if snap.settled_now:
        void_bit = (
            f" (из них возвратов: {snap.voids_now})" if snap.voids_now else ""
        )
        parts.append(f"Только что посчитали новых матчей: {snap.settled_now}{void_bit}.")
    else:
        parts.append("Новых завершённых матчей по нашим сигналам сейчас нет.")

    parts.append(f"Всего уже посчитано ставок: {snap.n}.")
    parts.append(f"Ещё ждут своего матча: {snap.pending}.")

    if snap.n > 0:
        parts.append("")
        parts.append(f"Зашло из посчитанных: {_pct(snap.hit_rate)}.")
        parts.append(
            f"В среднем мы ожидали захода около {_pct(snap.mean_model_prob)}."
        )
        if snap.mean_model_prob is not None and snap.hit_rate is not None:
            gap = snap.mean_model_prob - snap.hit_rate
            if gap > 0.03:
                parts.append(
                    "Пока факты чуть скромнее наших оценок — рано паниковать, "
                    "выборки ещё мало."
                )
            elif gap < -0.03:
                parts.append(
                    "Пока заходит чуть чаще, чем мы закладывали — тоже рано радоваться, "
                    "нужно больше матчей."
                )
            else:
                parts.append("Пока оценка и факты идут примерно рядом.")
        if snap.mean_clv is not None:
            # Keep CLV only if present, in plain words
            if snap.mean_clv > 0:
                parts.append(
                    "К моменту начала матчей линия в среднем двигалась в нашу пользу."
                )
            elif snap.mean_clv < 0:
                parts.append(
                    "К моменту начала матчей линия в среднем двигалась не в нашу пользу."
                )
    else:
        parts.append("")
        parts.append(
            "Пока почти нечего считать. О плюсе или минусе системы говорить рано."
        )

    parts.append("")
    if snap.n < 80:
        parts.append(
            f"Мы в режиме наблюдения: копим честную статистику "
            f"(ориентир — примерно 80–100 закрытых ставок). Сейчас {snap.n}. "
            "Правила из‑за эмоций не меняем."
        )
    else:
        parts.append(
            "Выборки уже достаточно, чтобы спокойно смотреть, не врёт ли нам оценка. "
            "Без спешки менять правила."
        )
    parts.append(pick_closing())
    parts.append(f"⚠️ {pick_disclaimer()}")
    return "\n".join(parts)
