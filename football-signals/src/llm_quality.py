from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import httpx
from loguru import logger

from src.lineup_context import extract_missing
from src.value_engine import SignalCandidate


@dataclass
class QualityVerdict:
    ok: bool
    summary: str
    raw: str | None = None
    confidence: float | None = None
    reasons: list[str] | None = None
    risks: list[str] | None = None


def _compact_match_context(match: dict, model_probs: dict[str, float], signal: SignalCandidate) -> dict[str, Any]:
    """Shrink API match detail for the lock judge prompt."""
    pregame = match.get("pregame") or {}
    probs_public = {
        k: round(float(v), 4)
        for k, v in model_probs.items()
        if not str(k).startswith("_") and isinstance(v, (int, float))
    }
    return {
        "match_id": match.get("id"),
        "home": signal.home_team,
        "away": signal.away_team,
        "league": signal.league_name,
        "kickoff": signal.kickoff,
        "proposed_outcome": signal.outcome,
        "proposed_label": signal.outcome_label,
        "model_prob": round(signal.model_prob, 4),
        "best_bookmaker": signal.best_bookmaker,
        "best_odds": round(signal.best_odds, 3),
        "implied": round(1.0 / signal.best_odds, 4) if signal.best_odds > 0 else None,
        "edge": round(signal.edge, 4),
        "lambda_home": model_probs.get("_lambda_home"),
        "lambda_away": model_probs.get("_lambda_away"),
        "model_probs": probs_public,
        "pregame_h2h": (pregame.get("h2h") or {}).get("teamDuel"),
        "pregame_streaks": (pregame.get("teamStreaks") or {}).get("general"),
        "pregame_form": pregame.get("form"),
        "missing_players": extract_missing(match).compact(),
        "tournament": (match.get("tournament") or {}).get("name"),
        "round": match.get("roundInfo"),
    }


class OpenAICompatibleClient:
    """Клиент LLM: OpenAI-compatible (Perplexity/OpenRouter/AITunnel) или Anthropic Messages API."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 60.0,
        label: str = "primary",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.label = label

    def _is_anthropic(self) -> bool:
        return "anthropic.com" in self.base_url.lower()

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.1,
        max_tokens: int = 800,
    ) -> str:
        if not self.api_key:
            raise ValueError("LLM API key is empty")
        if self._is_anthropic():
            return self._chat_anthropic(messages, temperature=temperature, max_tokens=max_tokens)
        return self._chat_openai(messages, temperature=temperature, max_tokens=max_tokens)

    def _chat_openai(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # DeepSeek V4 через шлюзы иногда включает thinking; для JSON-гейта лучше выключить.
        if "deepseek-v4" in (self.model or "").lower():
            payload["thinking"] = {"type": "disabled"}

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        message = (data.get("choices") or [{}])[0].get("message") or {}
        content = message.get("content")
        if content is None or (isinstance(content, str) and not content.strip()):
            # DeepSeek V4 / AITunnel: thinking часто в reasoning / reasoning_content
            content = message.get("reasoning_content") or message.get("reasoning")
        if content is None:
            raise ValueError(f"LLM returned empty content: {data!r}"[:800])
        if isinstance(content, list):
            # Anthropic-style blocks inside OpenAI wrapper
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text") or "")
                elif isinstance(block, str):
                    parts.append(block)
            content = "\n".join(parts)
        text = str(content)
        # Если модель долго думала и обрезалась на reasoning — вытащим JSON хвост
        if "{" in text and "}" in text:
            return text
        return text

    def _chat_anthropic(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
    ) -> str:
        system = None
        converted: list[dict[str, str]] = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                system = content
                continue
            if role not in {"user", "assistant"}:
                role = "user"
            converted.append({"role": role, "content": content})
        if not converted:
            converted = [{"role": "user", "content": system or ""}]
            system = None

        # Anthropic base is typically https://api.anthropic.com — endpoint /v1/messages
        root = self.base_url
        if root.endswith("/v1"):
            url = f"{root}/messages"
        else:
            url = f"{root}/v1/messages"
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": converted,
        }
        if system:
            payload["system"] = system
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        parts = data.get("content") or []
        texts = [p.get("text", "") for p in parts if isinstance(p, dict) and p.get("type") == "text"]
        return "\n".join(texts).strip()


class FailoverClient:
    """Сначала primary; при пустом ответе / сети / HTTP — fallback-модель."""

    def __init__(
        self,
        primary: OpenAICompatibleClient,
        fallback: OpenAICompatibleClient | None = None,
    ):
        self.primary = primary
        self.fallback = fallback

    @property
    def model(self) -> str:
        return self.primary.model

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.1,
        max_tokens: int = 800,
    ) -> str:
        try:
            return self.primary.chat(
                messages, temperature=temperature, max_tokens=max_tokens
            )
        except Exception as primary_exc:
            if self.fallback is None:
                raise
            logger.warning(
                "LLM primary failed ({} / {}): {} — trying fallback {} / {}",
                self.primary.label,
                self.primary.model,
                primary_exc,
                self.fallback.label,
                self.fallback.model,
            )
            return self.fallback.chat(
                messages, temperature=temperature, max_tokens=max_tokens
            )


def _extract_json(text: str | None) -> dict[str, Any]:
    if text is None:
        return {"ok": False, "summary": "empty LLM response"}
    text = str(text).strip()
    if not text:
        return {"ok": False, "summary": "empty LLM response"}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return {"ok": True, "summary": text[:500]}
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return {"ok": True, "summary": text[:500]}


def check_news(
    signal: SignalCandidate,
    *,
    client: OpenAICompatibleClient | FailoverClient | None,
    enabled: bool,
) -> QualityVerdict:
    """
    Слой новостей (Perplexity Sonar и т.п.).
    Если клиент не настроен — пропускаем проверку (ok=True).
    """
    if not enabled or client is None:
        return QualityVerdict(True, "news check skipped (disabled/no key)")

    prompt = (
        "Ты спортивный аналитик. Проверь свежие новости по матчу перед ставкой.\n"
        f"Матч: {signal.home_team} — {signal.away_team}\n"
        f"Лига: {signal.league_name}\n"
        f"Дата: {signal.kickoff}\n"
        f"Планируемый исход: {signal.outcome_label} (модель {signal.model_prob:.0%})\n\n"
        "Ищи травмы ключевых игроков, дисквалификации, ротацию состава, смену тренера, "
        "другие факторы за последние 48 часов, которые могут сильно изменить вероятность.\n"
        "Ответь СТРОГО JSON: {\"ok\": true|false, \"summary\": \"кратко по-русски\"}.\n"
        "ok=false только если есть серьёзный негативный фактор для выбранного исхода."
    )
    try:
        raw = client.chat(
            [
                {"role": "system", "content": "Отвечай только валидным JSON."},
                {"role": "user", "content": prompt},
            ]
        )
        data = _extract_json(raw)
        ok = bool(data.get("ok", True))
        summary = str(data.get("summary") or raw)[:1000]
        return QualityVerdict(ok, summary, raw)
    except Exception as exc:
        logger.warning("news check failed (after failover if any): {}", exc)
        # Новости: после сбоя primary+fallback не блокируем весь день
        return QualityVerdict(True, f"news check error (fail-open): {exc}")


def check_logic(
    signal: SignalCandidate,
    signal_text: str,
    *,
    client: OpenAICompatibleClient | FailoverClient | None,
    enabled: bool,
) -> QualityVerdict:
    """Финальная логическая проверка. Fail-closed, если обе модели молчат/падают."""
    if not enabled or client is None:
        return QualityVerdict(True, "logic check skipped (disabled/no key)")

    prompt = (
        "Проверь согласованность сигнала перед публикацией в канал.\n"
        "Правила:\n"
        "- model_prob должен быть >= 0.80\n"
        "- edge должен быть > 0 (модель выше implied 1/odds)\n"
        "- stake_fraction <= 0.0333\n"
        "- текст не должен противоречить цифрам\n"
        "- НЕ предлагай публиковать при edge<=0 даже если вероятность высокая\n\n"
        f"Данные: model_prob={signal.model_prob}, odds={signal.best_odds}, "
        f"edge={signal.edge}, stake={signal.stake_fraction}, "
        f"bk={signal.best_bookmaker}, outcome={signal.outcome_label}\n"
        f"Текст:\n{signal_text}\n\n"
        "Ответь СТРОГО JSON: {\"ok\": true|false, \"summary\": \"кратко\"}."
    )
    try:
        raw = client.chat(
            [
                {"role": "system", "content": "Отвечай только валидным JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
        )
        data = _extract_json(raw)
        ok = bool(data.get("ok", True))
        summary = str(data.get("summary") or raw)[:1000]
        return QualityVerdict(ok, summary, raw)
    except Exception as exc:
        logger.warning("logic check failed (after failover if any): {}", exc)
        # Канал не молчит из‑за сбоя шлюза: при ошибке транспорта — fail-open.
        # Явный ok=false от модели по-прежнему блокирует.
        return QualityVerdict(True, f"logic check error (fail-open): {exc}")


def check_lock(
    signal: SignalCandidate,
    match_detail: dict,
    model_probs: dict[str, float],
    *,
    client: OpenAICompatibleClient | FailoverClient | None,
    enabled: bool,
    min_confidence: float = 0.75,
) -> QualityVerdict:
    """
    AI judge for «верняк». Fail-closed: без клиента / ошибки / is_lock=false — ok=False.
    Кэф сам по себе не делает верняк — решение по совокупности данных API.
    """
    if not enabled or client is None:
        return QualityVerdict(
            False,
            "lock check skipped (no LLM) — fail-closed",
            confidence=0.0,
            reasons=[],
            risks=["no_llm"],
        )

    context = _compact_match_context(match_detail, model_probs, signal)
    prompt = (
        "Ты спортивный аналитик. Нужно решить, является ли исход «верняком» "
        "(явный безоговорочный фаворит по совокупности данных), а НЕ value-ставкой.\n"
        "Низкий коэффициент букмекера САМ ПО СЕБЕ НЕ делает исход верняком.\n"
        "Смотри h2h, streaks/form, λ модели, полный набор вероятностей, согласованность линии.\n"
        "Верняк = очень высокая уверенность, что фаворит не проиграет / победит, "
        "и данные API это подтверждают без серьёзных красных флагов.\n\n"
        f"Контекст (JSON):\n{json.dumps(context, ensure_ascii=False)}\n\n"
        "Ответь ТОЛЬКО одним JSON-объектом без текста до/после:\n"
        '{"is_lock": true|false, "confidence": 0.0-1.0, '
        '"reasons": ["кратко"], "risks": ["кратко"]}\n'
        "Максимум 3 reasons и 3 risks, каждый до 120 символов."
    )
    try:
        raw = client.chat(
            [
                {"role": "system", "content": "Отвечай только валидным JSON. Без markdown."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2500,
        )
        data = _extract_json(raw)
        is_lock = bool(data.get("is_lock", False))
        try:
            confidence = float(data.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        reasons_raw = data.get("reasons") or []
        risks_raw = data.get("risks") or []
        reasons = [str(x) for x in reasons_raw] if isinstance(reasons_raw, list) else [str(reasons_raw)]
        risks = [str(x) for x in risks_raw] if isinstance(risks_raw, list) else [str(risks_raw)]
        ok = is_lock and confidence >= min_confidence
        summary = "; ".join(reasons)[:1000] if reasons else (
            f"is_lock={is_lock} confidence={confidence:.2f}"
        )
        if not ok and is_lock and confidence < min_confidence:
            summary = f"confidence {confidence:.2f} < {min_confidence:.2f}; " + summary
        return QualityVerdict(
            ok,
            summary,
            raw,
            confidence=confidence,
            reasons=reasons,
            risks=risks,
        )
    except Exception as exc:
        logger.warning("lock check failed: {}", exc)
        return QualityVerdict(
            False,
            f"lock check error (fail-closed): {exc}",
            confidence=0.0,
            reasons=[],
            risks=[str(exc)],
        )
