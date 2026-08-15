from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def _split_csv(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    api_sport_base_url: str
    api_sport_key: str
    api_sport_sport_slug: str
    bookmakers_whitelist: list[str]
    max_bot_token: str
    max_channel_chat_id: str
    publish_mode: str
    min_model_probability: float
    min_edge: float
    stake_hard_cap_fraction: float
    kelly_fraction_mode: str
    bankroll_amount: float
    timezone: str
    database_url: str
    leagues_whitelist_path: Path
    # Odds spread anomaly threshold (absolute odds points, e.g. 0.8)
    odds_spread_anomaly_threshold: float
    # LLM quality gate
    llm_quality_enabled: bool
    news_llm_enabled: bool
    news_llm_api_key: str
    news_llm_base_url: str
    news_llm_model: str
    news_llm_fallback_api_key: str
    news_llm_fallback_base_url: str
    news_llm_fallback_model: str
    logic_llm_enabled: bool
    logic_llm_api_key: str
    logic_llm_base_url: str
    logic_llm_model: str
    logic_llm_fallback_api_key: str
    logic_llm_fallback_base_url: str
    logic_llm_fallback_model: str
    # Lock («верняк») stream
    lock_signals_enabled: bool
    lock_min_model_probability: float
    lock_odds_min: float
    lock_odds_max: float
    lock_min_lambda_gap: float
    lock_min_h2h_games: int
    lock_min_h2h_share: float
    lock_ai_min_confidence: float
    lock_stake_fraction: float
    lock_llm_api_key: str
    lock_llm_base_url: str
    lock_llm_model: str
    lock_llm_fallback_api_key: str
    lock_llm_fallback_base_url: str
    lock_llm_fallback_model: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    db_url = os.getenv("DATABASE_URL", "sqlite:///data/signals.db")
    if db_url.startswith("sqlite:///"):
        rel = db_url.replace("sqlite:///", "", 1)
        abs_path = (ROOT / rel).resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        db_url = f"sqlite:///{abs_path.as_posix()}"

    logic_key = os.getenv("LOGIC_LLM_API_KEY", "")
    logic_base = os.getenv("LOGIC_LLM_BASE_URL", "https://api.aitunnel.ru/v1").rstrip("/")
    logic_model = os.getenv("LOGIC_LLM_MODEL", "deepseek-chat")
    logic_fb_key = os.getenv("LOGIC_LLM_FALLBACK_API_KEY", "")
    logic_fb_base = (
        os.getenv("LOGIC_LLM_FALLBACK_BASE_URL") or logic_base
    ).rstrip("/")
    logic_fb_model = os.getenv("LOGIC_LLM_FALLBACK_MODEL", "")

    return Settings(
        api_sport_base_url=os.getenv("API_SPORT_BASE_URL", "https://api.api-sport.ru").rstrip("/"),
        api_sport_key=os.getenv("API_SPORT_KEY", ""),
        api_sport_sport_slug=os.getenv("API_SPORT_SPORT_SLUG", "football"),
        bookmakers_whitelist=_split_csv(
            os.getenv("BOOKMAKERS_WHITELIST", "marathon,melbet,betboom,pari")
        ),
        max_bot_token=os.getenv("MAX_BOT_TOKEN", ""),
        max_channel_chat_id=os.getenv("MAX_CHANNEL_CHAT_ID", ""),
        publish_mode=os.getenv("PUBLISH_MODE", "dry_run").lower(),
        min_model_probability=float(os.getenv("MIN_MODEL_PROBABILITY", "0.80")),
        min_edge=float(os.getenv("MIN_EDGE", "0.02")),
        stake_hard_cap_fraction=float(os.getenv("STAKE_HARD_CAP_FRACTION", "0.0333")),
        kelly_fraction_mode=os.getenv("KELLY_FRACTION_MODE", "quarter").lower(),
        bankroll_amount=float(os.getenv("BANKROLL_AMOUNT", "30000")),
        timezone=os.getenv("TIMEZONE", "Europe/Moscow"),
        database_url=db_url,
        leagues_whitelist_path=ROOT / "config" / "leagues_whitelist.yaml",
        odds_spread_anomaly_threshold=float(os.getenv("ODDS_SPREAD_ANOMALY_THRESHOLD", "0.80")),
        llm_quality_enabled=_bool(os.getenv("LLM_QUALITY_ENABLED"), False),
        news_llm_enabled=_bool(os.getenv("NEWS_LLM_ENABLED"), False),
        news_llm_api_key=os.getenv("NEWS_LLM_API_KEY", ""),
        news_llm_base_url=os.getenv(
            "NEWS_LLM_BASE_URL", "https://api.perplexity.ai"
        ).rstrip("/"),
        news_llm_model=os.getenv("NEWS_LLM_MODEL", "sonar"),
        news_llm_fallback_api_key=os.getenv("NEWS_LLM_FALLBACK_API_KEY", ""),
        news_llm_fallback_base_url=(
            os.getenv("NEWS_LLM_FALLBACK_BASE_URL")
            or os.getenv("NEWS_LLM_BASE_URL", "https://api.perplexity.ai")
        ).rstrip("/"),
        news_llm_fallback_model=os.getenv("NEWS_LLM_FALLBACK_MODEL", ""),
        logic_llm_enabled=_bool(os.getenv("LOGIC_LLM_ENABLED"), False),
        logic_llm_api_key=logic_key,
        logic_llm_base_url=logic_base,
        logic_llm_model=logic_model,
        logic_llm_fallback_api_key=logic_fb_key,
        logic_llm_fallback_base_url=logic_fb_base,
        logic_llm_fallback_model=logic_fb_model,
        lock_signals_enabled=_bool(os.getenv("LOCK_SIGNALS_ENABLED"), True),
        lock_min_model_probability=float(os.getenv("LOCK_MIN_MODEL_PROBABILITY", "0.78")),
        lock_odds_min=float(os.getenv("LOCK_ODDS_MIN", "1.12")),
        lock_odds_max=float(os.getenv("LOCK_ODDS_MAX", "1.45")),
        lock_min_lambda_gap=float(os.getenv("LOCK_MIN_LAMBDA_GAP", "0.35")),
        lock_min_h2h_games=int(os.getenv("LOCK_MIN_H2H_GAMES", "5")),
        lock_min_h2h_share=float(os.getenv("LOCK_MIN_H2H_SHARE", "0.65")),
        lock_ai_min_confidence=float(os.getenv("LOCK_AI_MIN_CONFIDENCE", "0.75")),
        lock_stake_fraction=float(os.getenv("LOCK_STAKE_FRACTION", str(1.0 / 60.0))),
        # Default lock LLM = same as logic LLM
        lock_llm_api_key=os.getenv("LOCK_LLM_API_KEY") or logic_key,
        lock_llm_base_url=(
            os.getenv("LOCK_LLM_BASE_URL") or logic_base
        ).rstrip("/"),
        lock_llm_model=os.getenv("LOCK_LLM_MODEL") or logic_model,
        lock_llm_fallback_api_key=os.getenv("LOCK_LLM_FALLBACK_API_KEY") or logic_fb_key,
        lock_llm_fallback_base_url=(
            os.getenv("LOCK_LLM_FALLBACK_BASE_URL") or logic_fb_base
        ).rstrip("/"),
        lock_llm_fallback_model=os.getenv("LOCK_LLM_FALLBACK_MODEL") or logic_fb_model,
    )


@lru_cache(maxsize=1)
def load_leagues_whitelist() -> dict[int, dict]:
    path = get_settings().leagues_whitelist_path
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    out: dict[int, dict] = {}
    for item in raw.get("leagues", []):
        league_id = int(item["id"])
        out[league_id] = item
    return out
