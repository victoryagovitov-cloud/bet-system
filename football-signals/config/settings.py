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
    stake_hard_cap_fraction: float
    kelly_fraction_mode: str
    bankroll_amount: float
    timezone: str
    database_url: str
    leagues_whitelist_path: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    db_url = os.getenv("DATABASE_URL", "sqlite:///data/signals.db")
    if db_url.startswith("sqlite:///"):
        rel = db_url.replace("sqlite:///", "", 1)
        abs_path = (ROOT / rel).resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        db_url = f"sqlite:///{abs_path.as_posix()}"

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
        stake_hard_cap_fraction=float(os.getenv("STAKE_HARD_CAP_FRACTION", "0.0333")),
        kelly_fraction_mode=os.getenv("KELLY_FRACTION_MODE", "quarter").lower(),
        bankroll_amount=float(os.getenv("BANKROLL_AMOUNT", "30000")),
        timezone=os.getenv("TIMEZONE", "Europe/Moscow"),
        database_url=db_url,
        leagues_whitelist_path=ROOT / "config" / "leagues_whitelist.yaml",
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
