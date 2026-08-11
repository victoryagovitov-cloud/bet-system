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
from src import (
    llm_quality,
    max_publisher,
    probability_model,
    signal_formatter,
    stake_engine,
    value_engine,
)


def _news_client(settings):
    if not (settings.llm_quality_enabled and settings.news_llm_enabled and settings.news_llm_api_key):
        return None
    return llm_quality.OpenAICompatibleClient(
        api_key=settings.news_llm_api_key,
        base_url=settings.news_llm_base_url,
        model=settings.news_llm_model,
    )


def _logic_client(settings):
    if not (settings.llm_quality_enabled and settings.logic_llm_enabled and settings.logic_llm_api_key):
        return None
    return llm_quality.OpenAICompatibleClient(
        api_key=settings.logic_llm_api_key,
        base_url=settings.logic_llm_base_url,
        model=settings.logic_llm_model,
    )


def run_daily_pipeline(target_date: date | None = None) -> list[value_engine.SignalCandidate]:
    settings = get_settings()
    target_date = target_date or date.today()
    bookmakers = settings.bookmakers_whitelist
    repo = SignalRepository(settings.database_url)
    signals: list[value_engine.SignalCandidate] = []
    news_client = _news_client(settings)
    logic_client = _logic_client(settings)
    matches_with_odds = 0
    matches_in_whitelist = 0

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

        matches_with_odds = len(matches)
        logger.info("matches with RU BK odds: {}", matches_with_odds)

        allowed = []
        for m in matches:
            league_id = ((m.get("tournament") or {}).get("id"))
            if not is_league_allowed(league_id):
                continue
            if m.get("status") != "notstarted":
                continue
            allowed.append(m)

        matches_in_whitelist = len(allowed)
        logger.info("matches after league whitelist: {}", matches_in_whitelist)

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
                    "skip match={} outcome={} — kelly=0 (no positive edge)",
                    match_id,
                    signal.outcome,
                )
                continue
            signal.stake_fraction = stake

            existing = repo.get_by_match_outcome(signal.match_id, signal.outcome)
            if existing is not None:
                if signal.best_odds > (existing.best_odds or 0):
                    repo.note_odds_improvement(
                        signal.match_id, signal.outcome, signal.best_odds, signal.best_bookmaker
                    )
                    logger.info(
                        "dup skip (odds improved logged) match={} {} {:.2f}->{:.2f}",
                        signal.match_id,
                        signal.outcome,
                        existing.best_odds,
                        signal.best_odds,
                    )
                else:
                    logger.info(
                        "dup skip match={} outcome={} already status={}",
                        signal.match_id,
                        signal.outcome,
                        existing.status,
                    )
                continue

            odds_min, odds_max, odds_spread = value_engine.odds_spread_for_outcome(
                detail.get("oddsBk") or {}, bookmakers, signal.outcome
            )
            anomaly = bool(
                odds_spread is not None
                and odds_spread >= settings.odds_spread_anomaly_threshold
            )
            if anomaly:
                logger.warning(
                    "odds spread anomaly match={} outcome={} min={} max={} spread={}",
                    signal.match_id,
                    signal.outcome,
                    odds_min,
                    odds_max,
                    odds_spread,
                )

            text = signal_formatter.format_signal(signal, settings.bankroll_amount)

            news = llm_quality.check_news(
                signal,
                client=news_client,
                enabled=settings.llm_quality_enabled and settings.news_llm_enabled,
            )
            if not news.ok:
                repo.save_signal(
                    signal,
                    status="blocked_news",
                    odds_min=odds_min,
                    odds_max=odds_max,
                    odds_spread=odds_spread,
                    odds_spread_anomaly=anomaly,
                    news_check_ok=False,
                    news_check_summary=news.summary,
                )
                logger.warning("blocked by news: {} — {}", signal.match_id, news.summary)
                continue

            logic = llm_quality.check_logic(
                signal,
                text,
                client=logic_client,
                enabled=settings.llm_quality_enabled and settings.logic_llm_enabled,
            )
            if not logic.ok:
                repo.save_signal(
                    signal,
                    status="blocked_logic",
                    odds_min=odds_min,
                    odds_max=odds_max,
                    odds_spread=odds_spread,
                    odds_spread_anomaly=anomaly,
                    news_check_ok=news.ok,
                    news_check_summary=news.summary,
                    logic_check_ok=False,
                    logic_check_summary=logic.summary,
                )
                logger.warning("blocked by logic: {} — {}", signal.match_id, logic.summary)
                continue

            publish_ref = max_publisher.publish_signal(
                text,
                chat_id=settings.max_channel_chat_id,
                token=settings.max_bot_token,
                publish_mode=settings.publish_mode,
                match_id=signal.match_id,
            )
            repo.save_signal(
                signal,
                publish_ref=publish_ref,
                status="published",
                odds_min=odds_min,
                odds_max=odds_max,
                odds_spread=odds_spread,
                odds_spread_anomaly=anomaly,
                news_check_ok=news.ok,
                news_check_summary=news.summary,
                logic_check_ok=logic.ok,
                logic_check_summary=logic.summary,
            )
            signals.append(signal)
            logger.info(
                "SIGNAL {} {} {} @{} ({}) edge={:.1%} stake={:.2%} anomaly={}",
                signal.home_team,
                signal.away_team,
                signal.outcome_label,
                signal.best_odds,
                signal.best_bookmaker,
                signal.edge,
                signal.stake_fraction,
                anomaly,
            )

    digest = signal_formatter.format_daily_digest(
        target_date=target_date,
        matches_with_odds=matches_with_odds,
        matches_in_whitelist=matches_in_whitelist,
        signals=signals,
    )
    digest_ref = max_publisher.publish_signal(
        digest,
        chat_id=settings.max_channel_chat_id,
        token=settings.max_bot_token,
        publish_mode=settings.publish_mode,
        match_id=None,
    )
    logger.info("daily digest published ref={} signals={}", digest_ref, len(signals))
    logger.info("pipeline done signals={}", len(signals))
    return signals
