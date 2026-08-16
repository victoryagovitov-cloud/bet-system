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
from src.season_strength import attach_season_stats, index_standings



def _news_client(settings):
    if not (settings.llm_quality_enabled and settings.news_llm_enabled and settings.news_llm_api_key):
        return None
    primary = llm_quality.OpenAICompatibleClient(
        api_key=settings.news_llm_api_key,
        base_url=settings.news_llm_base_url,
        model=settings.news_llm_model,
        label="news-primary",
    )
    fallback = None
    if settings.news_llm_fallback_api_key and settings.news_llm_fallback_model:
        fallback = llm_quality.OpenAICompatibleClient(
            api_key=settings.news_llm_fallback_api_key,
            base_url=settings.news_llm_fallback_base_url,
            model=settings.news_llm_fallback_model,
            label="news-fallback",
        )
    return llm_quality.FailoverClient(primary, fallback)


def _logic_client(settings):
    if not (settings.llm_quality_enabled and settings.logic_llm_enabled and settings.logic_llm_api_key):
        return None
    primary = llm_quality.OpenAICompatibleClient(
        api_key=settings.logic_llm_api_key,
        base_url=settings.logic_llm_base_url,
        model=settings.logic_llm_model,
        label="logic-primary",
    )
    fallback = None
    if settings.logic_llm_fallback_api_key and settings.logic_llm_fallback_model:
        fallback = llm_quality.OpenAICompatibleClient(
            api_key=settings.logic_llm_fallback_api_key,
            base_url=settings.logic_llm_fallback_base_url,
            model=settings.logic_llm_fallback_model,
            label="logic-fallback",
        )
    return llm_quality.FailoverClient(primary, fallback)


def _lock_client(settings):
    """Lock AI uses dedicated LOCK_LLM_* (defaults to LOGIC_*). Fail-closed if no key."""
    if not settings.lock_signals_enabled:
        return None
    if not settings.lock_llm_api_key:
        return None
    primary = llm_quality.OpenAICompatibleClient(
        api_key=settings.lock_llm_api_key,
        base_url=settings.lock_llm_base_url,
        model=settings.lock_llm_model,
        label="lock-primary",
    )
    fallback = None
    if settings.lock_llm_fallback_api_key and settings.lock_llm_fallback_model:
        fallback = llm_quality.OpenAICompatibleClient(
            api_key=settings.lock_llm_fallback_api_key,
            base_url=settings.lock_llm_fallback_base_url,
            model=settings.lock_llm_fallback_model,
            label="lock-fallback",
        )
    return llm_quality.FailoverClient(primary, fallback)


def _try_publish(
    *,
    signal: value_engine.SignalCandidate,
    detail: dict,
    model_probs: dict,
    settings,
    repo: SignalRepository,
    bookmakers: list[str],
    news_client,
    logic_client,
    lock_client,
) -> value_engine.SignalCandidate | None:
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
        return None

    odds_min, odds_max, odds_spread = value_engine.odds_spread_for_outcome(
        detail.get("oddsBk") or {}, bookmakers, signal.outcome
    )
    anomaly = bool(
        odds_spread is not None and odds_spread >= settings.odds_spread_anomaly_threshold
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

    kind = (signal.signal_kind or "value").lower()

    if kind == "lock":
        lock = llm_quality.check_lock(
            signal,
            detail,
            model_probs,
            client=lock_client,
            enabled=True,
            min_confidence=settings.lock_ai_min_confidence,
        )
        if not lock.ok:
            repo.save_signal(
                signal,
                status="blocked_lock",
                odds_min=odds_min,
                odds_max=odds_max,
                odds_spread=odds_spread,
                odds_spread_anomaly=anomaly,
                logic_check_ok=False,
                logic_check_summary=lock.summary,
            )
            logger.info(
                "lock rejected match={} outcome={} — {}",
                signal.match_id,
                signal.outcome,
                lock.summary,
            )
            return None
        signal.lock_reasons = list(lock.reasons or [])
        signal.lock_confidence = lock.confidence

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
        return None

    if kind != "lock":
        logic = llm_quality.check_logic(
            signal,
            text,
            client=logic_client,
            enabled=settings.llm_quality_enabled and settings.logic_llm_enabled,
            match_detail=detail,
            bookmakers=bookmakers,
            model_probs=model_probs,
            max_edge=settings.max_edge,
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
            return None
        logic_ok, logic_summary = logic.ok, logic.summary
    else:
        logic_ok, logic_summary = True, "; ".join(signal.lock_reasons or [])[:1000]

    # Re-format lock text after reasons filled
    if kind == "lock":
        text = signal_formatter.format_signal(signal, settings.bankroll_amount)

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
        logic_check_ok=logic_ok,
        logic_check_summary=logic_summary,
    )
    logger.info(
        "SIGNAL [{}] {} {} {} @{} ({}) edge={:.1%} stake={:.2%} anomaly={}",
        kind.upper(),
        signal.home_team,
        signal.away_team,
        signal.outcome_label,
        signal.best_odds,
        signal.best_bookmaker,
        signal.edge,
        signal.stake_fraction,
        anomaly,
    )
    return signal


def run_daily_pipeline(
    target_date: date | list[date] | None = None,
) -> list[value_engine.SignalCandidate]:
    """
    Прогон по одной или нескольким датам (по умолчанию вызывающий код задаёт today+tomorrow).
    В конце ВСЕГДА публикуется сводка — канал не молчит даже при 0 ставках.
    """
    settings = get_settings()
    if target_date is None:
        dates = [date.today()]
    elif isinstance(target_date, date):
        dates = [target_date]
    else:
        dates = list(target_date)
    if not dates:
        dates = [date.today()]

    bookmakers = settings.bookmakers_whitelist
    repo = SignalRepository(settings.database_url)
    signals: list[value_engine.SignalCandidate] = []
    news_client = _news_client(settings)
    logic_client = _logic_client(settings)
    lock_client = _lock_client(settings)
    matches_with_odds = 0
    matches_in_whitelist = 0
    label = ",".join(d.isoformat() for d in dates)
    standings_cache: dict[int, dict] = {}

    logger.info("pipeline start dates={} bookmakers={}", label, bookmakers)

    def _season_index_for(tournament_id: int | None) -> dict:
        if not tournament_id:
            return {}
        tid = int(tournament_id)
        if tid not in standings_cache:
            try:
                standings_cache[tid] = client.get_tournament_standings(tid)
                logger.info(
                    "standings loaded tournament={} teams~={}",
                    tid,
                    len(index_standings(standings_cache[tid])),
                )
            except ApiSportError as exc:
                logger.warning("standings unavailable tournament={}: {}", tid, exc)
                standings_cache[tid] = {}
        return index_standings(standings_cache.get(tid) or {})

    with ApiSportClient(
        settings.api_sport_base_url,
        settings.api_sport_key,
        settings.api_sport_sport_slug,
    ) as client:
        for day in dates:
            try:
                matches = client.get_matches(day, bookmakers)
            except ApiSportError as exc:
                logger.error("failed to fetch matches for {}: {}", day, exc)
                continue

            matches_with_odds += len(matches)
            logger.info("date={} matches with RU BK odds: {}", day, len(matches))

            allowed = []
            for m in matches:
                league_id = ((m.get("tournament") or {}).get("id"))
                if not is_league_allowed(league_id):
                    continue
                if m.get("status") != "notstarted":
                    continue
                allowed.append(m)

            matches_in_whitelist += len(allowed)
            logger.info("date={} after league whitelist: {}", day, len(allowed))

            value_pool: list[
                tuple[value_engine.SignalCandidate, dict, dict[str, float]]
            ] = []
            lock_pool: list[
                tuple[value_engine.SignalCandidate, dict, dict[str, float]]
            ] = []

            for m in allowed:
                match_id = m.get("id")
                try:
                    detail = client.get_match_detail(int(match_id), bookmakers)
                except ApiSportError as exc:
                    logger.warning("skip match {}: {}", match_id, exc)
                    continue

                tid = ((detail.get("tournament") or {}).get("id")) or (
                    (m.get("tournament") or {}).get("id")
                )
                attach_season_stats(detail, _season_index_for(tid))
                model_probs = probability_model.compute(detail)

                signal = value_engine.find_signal(
                    detail,
                    model_probs,
                    bookmakers,
                    min_model_probability=settings.min_model_probability,
                    min_edge=settings.min_edge,
                    max_edge=settings.max_edge,
                )
                if signal:
                    stake = stake_engine.calculate_stake_fraction(
                        signal.model_prob,
                        signal.best_odds,
                        kelly_mode=settings.kelly_fraction_mode,
                        hard_cap=settings.stake_hard_cap_fraction,
                    )
                    if stake <= 0:
                        logger.info(
                            "value kelly=0 match={} outcome={} — try lock path",
                            match_id,
                            signal.outcome,
                        )
                        signal = None
                    else:
                        signal.stake_fraction = stake
                        value_pool.append((signal, detail, model_probs))

                if signal is None and settings.lock_signals_enabled:
                    lock_signal = value_engine.find_lock_candidate(
                        detail,
                        model_probs,
                        bookmakers,
                        min_model_probability=settings.lock_min_model_probability,
                        odds_min=settings.lock_odds_min,
                        odds_max=settings.lock_odds_max,
                        min_lambda_gap=settings.lock_min_lambda_gap,
                        min_h2h_games=settings.lock_min_h2h_games,
                        min_h2h_share=settings.lock_min_h2h_share,
                    )
                    if lock_signal:
                        lock_signal.stake_fraction = (
                            stake_engine.calculate_lock_stake_fraction(
                                settings.lock_stake_fraction
                            )
                        )
                        lock_pool.append((lock_signal, detail, model_probs))
                elif signal is None and not settings.lock_signals_enabled:
                    logger.debug(
                        "no value and locks disabled match={} probs={}",
                        match_id,
                        probability_model.summarize_for_log(model_probs),
                    )

            value_pool.sort(key=lambda t: t[0].edge, reverse=True)
            max_n = max(0, int(settings.max_value_signals_per_run))
            selected_values = value_pool[:max_n]
            if len(value_pool) > max_n:
                logger.info(
                    "value cap: kept {}/{} candidates (max_edge filter already applied)",
                    max_n,
                    len(value_pool),
                )
            selected_match_ids = {s.match_id for s, _, _ in selected_values}

            for signal, detail, model_probs in selected_values:
                published = _try_publish(
                    signal=signal,
                    detail=detail,
                    model_probs=model_probs,
                    settings=settings,
                    repo=repo,
                    bookmakers=bookmakers,
                    news_client=news_client,
                    logic_client=logic_client,
                    lock_client=lock_client,
                )
                if published:
                    signals.append(published)

            for lock_signal, detail, model_probs in lock_pool:
                if lock_signal.match_id in selected_match_ids:
                    continue
                published = _try_publish(
                    signal=lock_signal,
                    detail=detail,
                    model_probs=model_probs,
                    settings=settings,
                    repo=repo,
                    bookmakers=bookmakers,
                    news_client=news_client,
                    logic_client=logic_client,
                    lock_client=lock_client,
                )
                if published:
                    signals.append(published)

    digest_date = dates[0] if len(dates) == 1 else dates[-1]
    pending = len(repo.unsettled())
    digest = signal_formatter.format_daily_digest(
        target_date=digest_date,
        matches_with_odds=matches_with_odds,
        matches_in_whitelist=matches_in_whitelist,
        signals=signals,
        date_window=dates if len(dates) > 1 else None,
        pending_settlement=pending,
    )
    digest_ref = max_publisher.publish_signal(
        digest,
        chat_id=settings.max_channel_chat_id,
        token=settings.max_bot_token,
        publish_mode=settings.publish_mode,
        match_id=None,
    )
    logger.info(
        "daily digest published ref={} signals={} pending_settlement={}",
        digest_ref,
        len(signals),
        pending,
    )
    logger.info("pipeline done signals={}", len(signals))
    return signals
