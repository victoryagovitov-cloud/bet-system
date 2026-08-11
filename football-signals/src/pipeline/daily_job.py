from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from loguru import logger

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import get_settings
from src.api_sport_client import ApiSportClient, ApiSportError
from src.db.repository import SignalRepository
from src.league_filter import is_league_allowed
from src import max_publisher, probability_model, signal_formatter, stake_engine, value_engine


def run_daily_pipeline(target_date: date | None = None) -> list[value_engine.SignalCandidate]:
    settings = get_settings()
    target_date = target_date or date.today()
    bookmakers = settings.bookmakers_whitelist
    repo = SignalRepository(settings.database_url)
    signals: list[value_engine.SignalCandidate] = []

    logger.info("pipeline start date={} bookmakers={}", target_date, bookmakers)

    with ApiSportClient(
        settings.api_sport_base_url,
        settings.api_sport_key,
        settings.api_sport_sport_slug,
    ) as client:
        try:
            matches = client.get_matches(target_date, bookmakers)
        except ApiSportError as exc:
            logger.error("failed to fetch matches: {}", exc)
            return []

        logger.info("matches with RU BK odds: {}", len(matches))

        allowed = []
        for m in matches:
            league_id = ((m.get("tournament") or {}).get("id"))
            if not is_league_allowed(league_id):
                continue
            if m.get("status") not in (None, "notstarted"):
                # MVP: только prematch
                if m.get("status") != "notstarted":
                    continue
            allowed.append(m)

        logger.info("matches after league whitelist: {}", len(allowed))

        for m in allowed:
            match_id = m.get("id")
            try:
                detail = client.get_match_detail(int(match_id), bookmakers)
            except ApiSportError as exc:
                logger.warning("skip match {}: {}", match_id, exc)
                continue

            model_probs = probability_model.compute(detail)
            signal = value_engine.find_signal(
                detail,
                model_probs,
                bookmakers,
                min_model_probability=settings.min_model_probability,
            )
            if not signal:
                logger.debug(
                    "no signal match={} probs={}",
                    match_id,
                    probability_model.summarize_for_log(model_probs),
                )
                continue

            stake = stake_engine.calculate_stake_fraction(
                signal.model_prob,
                signal.best_odds,
                kelly_mode=settings.kelly_fraction_mode,
                hard_cap=settings.stake_hard_cap_fraction,
            )
            if stake <= 0:
                logger.info(
                    "skip match={} outcome={} — kelly=0 (no positive edge after stake)",
                    match_id,
                    signal.outcome,
                )
                continue
            signal.stake_fraction = stake

            text = signal_formatter.format_signal(signal, settings.bankroll_amount)
            publish_ref = max_publisher.publish_signal(
                text,
                chat_id=settings.max_channel_chat_id,
                token=settings.max_bot_token,
                publish_mode=settings.publish_mode,
                match_id=signal.match_id,
            )
            repo.save_signal(signal, publish_ref=publish_ref)
            signals.append(signal)
            logger.info(
                "SIGNAL {} {} {} @{} ({}) edge={:.1%} stake={:.2%}",
                signal.home_team,
                signal.away_team,
                signal.outcome_label,
                signal.best_odds,
                signal.best_bookmaker,
                signal.edge,
                signal.stake_fraction,
            )

    logger.info("pipeline done signals={}", len(signals))
    return signals
