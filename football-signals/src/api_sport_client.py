from __future__ import annotations

import time
from datetime import date
from typing import Any

import httpx
from loguru import logger

BOOKMAKERS = ("marathon", "melbet", "betboom", "pari")


class ApiSportError(Exception):
    def __init__(self, message: str, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class ApiSportClient:
    """Клиент API-SPORT.ru: football matches + oddsBk + pregame."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        sport_slug: str = "football",
        timeout: float = 20.0,
        max_retries: int = 4,
    ):
        if not api_key:
            raise ValueError("API_SPORT_KEY is empty")
        self.base_url = base_url.rstrip("/")
        self.sport_slug = sport_slug
        self.max_retries = max_retries
        self._rate_log_left = 10
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": api_key},
            timeout=timeout,
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "ApiSportClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(self, method: str, path: str, params: dict | None = None) -> Any:
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            started = time.perf_counter()
            try:
                resp = self.client.request(method, path, params=params)
            except httpx.HTTPError as exc:
                last_exc = exc
                sleep_s = 2**attempt
                logger.warning("network error {} retry in {}s", exc, sleep_s)
                time.sleep(sleep_s)
                continue

            latency_ms = (time.perf_counter() - started) * 1000
            if self._rate_log_left > 0:
                rate_headers = {
                    k: v
                    for k, v in resp.headers.items()
                    if "rate" in k.lower() or "limit" in k.lower()
                }
                logger.info(
                    "API {} {} -> {} ({:.0f}ms) rate={}",
                    method,
                    path,
                    resp.status_code,
                    latency_ms,
                    rate_headers,
                )
                self._rate_log_left -= 1
            else:
                logger.debug("API {} {} -> {} ({:.0f}ms)", method, path, resp.status_code, latency_ms)

            if resp.status_code == 400:
                try:
                    payload = resp.json()
                except Exception:
                    payload = resp.text
                if isinstance(payload, dict) and payload.get("error") == "user_has_no_access":
                    raise ApiSportError(
                        "Тариф не покрывает football/oddsBk (user_has_no_access)",
                        status_code=400,
                        payload=payload,
                    )
                raise ApiSportError(f"Bad request: {payload}", status_code=400, payload=payload)

            if resp.status_code in (429, 500, 502, 503, 504):
                sleep_s = 2**attempt
                logger.warning("retryable status {} sleep {}s", resp.status_code, sleep_s)
                time.sleep(sleep_s)
                continue

            if resp.status_code >= 400:
                raise ApiSportError(
                    f"HTTP {resp.status_code}: {resp.text[:500]}",
                    status_code=resp.status_code,
                    payload=resp.text,
                )
            return resp.json()

        raise ApiSportError(f"Failed after retries: {last_exc}")

    @staticmethod
    def _has_whitelisted_odds(match: dict, bookmaker_ids: list[str]) -> bool:
        has_bk = match.get("hasBkOdds") or {}
        return any(bool(has_bk.get(bk)) for bk in bookmaker_ids)

    def get_matches(self, target_date: date, bookmaker_ids: list[str] | None = None) -> list[dict]:
        """
        GET /v2/{sport}/matches?date=YYYY-MM-DD&has_bk_odds=true
        + клиентский фильтр hasBkOdds по whitelist БК.
        """
        bookmaker_ids = bookmaker_ids or list(BOOKMAKERS)
        payload = self._request(
            "GET",
            f"/v2/{self.sport_slug}/matches",
            params={"date": target_date.isoformat(), "has_bk_odds": "true"},
        )
        matches = payload.get("matches") if isinstance(payload, dict) else payload
        if not isinstance(matches, list):
            raise ApiSportError(f"Unexpected matches payload type: {type(payload)}")

        filtered = [m for m in matches if self._has_whitelisted_odds(m, bookmaker_ids)]
        skipped = len(matches) - len(filtered)
        if skipped:
            logger.info("no RU bookmaker odds, skipped: {}", skipped)
        return filtered

    def get_match_detail(self, match_id: int, bookmaker_ids: list[str] | None = None) -> dict:
        bookmaker_ids = bookmaker_ids or list(BOOKMAKERS)
        return self._request(
            "GET",
            f"/v2/{self.sport_slug}/matches/{match_id}",
            params={
                "with_bk_odds": "true",
                "bookmaker_ids": ",".join(bookmaker_ids),
                "with_pregame": "true",
            },
        )

    def get_tournament_seasons(self, tournament_id: int) -> Any:
        return self._request(
            "GET",
            f"/v2/{self.sport_slug}/tournament/{tournament_id}/seasons",
        )

    def get_tournament_standings(self, tournament_id: int) -> dict:
        """
        GET /v2/{sport}/tournament/{id}/standings
        Таблица сезона: scoresFor / scoresAgainst / matches / points.
        """
        payload = self._request(
            "GET",
            f"/v2/{self.sport_slug}/tournament/{tournament_id}/standings",
            params={"locale": "ru"},
        )
        if not isinstance(payload, dict):
            raise ApiSportError(f"Unexpected standings payload: {type(payload)}")
        return payload

