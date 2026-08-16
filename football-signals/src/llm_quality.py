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


def _season_context(match: dict, model_probs: dict[str, float]) -> dict[str, Any]:
    """Compact season-table strength for LLM judges."""
    from src.season_strength import team_id_from_match

    by_team = match.get("_season_by_team") or {}
    used = bool(model_probs.get("_used_season_strength"))

    def pack(side: str) -> dict[str, Any] | None:
        tid = team_id_from_match(match, side)
        if tid is None:
            return None
        st = by_team.get(int(tid))
        if st is None:
            return {"team_id": tid, "in_table": False}
        return {
            "team_id": tid,
            "in_table": True,
            "position": st.position,
            "matches": st.matches,
            "points": st.points,
            "gf_pg": round(st.gf_pg, 3),
            "ga_pg": round(st.ga_pg, 3),
        }

    home = pack("home")
    away = pack("away")
    gap = None
    if (
        isinstance(home, dict)
        and isinstance(away, dict)
        and home.get("position") is not None
        and away.get("position") is not None
    ):
        gap = int(away["position"]) - int(home["position"])
    return {
        "used_in_model": used,
        "lambda_home": model_probs.get("_lambda_home"),
        "lambda_away": model_probs.get("_lambda_away"),
        "home": home,
        "away": away,
        "home_minus_away_position": gap,  # >0 ⇒ home выше в таблице
    }


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
        "season_strength": _season_context(match, model_probs),
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


def _best_odds_map(
    odds_bk: dict,
    bookmakers: list[str],
    outcomes: list[str],
) -> dict[str, dict[str, float | str]]:
    from src.value_engine import best_odds_across_bookmakers

    out: dict[str, dict[str, float | str]] = {}
    for outcome in outcomes:
        bk, odds = best_odds_across_bookmakers(odds_bk, bookmakers, outcome)
        if bk is None or odds is None or odds <= 1.0:
            continue
        out[outcome] = {
            "bk": bk,
            "odds": round(float(odds), 3),
            "implied": round(1.0 / float(odds), 4),
        }
    return out


def check_logic(
    signal: SignalCandidate,
    signal_text: str,
    *,
    client: OpenAICompatibleClient | FailoverClient | None,
    enabled: bool,
    match_detail: dict | None = None,
    bookmakers: list[str] | None = None,
    model_probs: dict[str, float] | None = None,
    max_edge: float = 0.15,
) -> QualityVerdict:
    """
    Стоп-кран для VALUE перед публикацией.
    Явный ok=false всегда блокирует. Fail-open только на транспортной ошибке LLM.
    """
    if not enabled or client is None:
        return QualityVerdict(True, "logic check skipped (disabled/no key)")

    implied = (1.0 / signal.best_odds) if signal.best_odds > 1.0 else None
    edge = float(signal.edge)

    # Hard stops in code (LLM is second layer, not the only one).
    if edge <= 0:
        return QualityVerdict(False, f"edge<=0 ({edge:.3f})")
    if edge > max_edge:
        return QualityVerdict(
            False,
            f"edge {edge:.1%} > max {max_edge:.0%} — слишком жирный, недоверие к модели",
        )
    if signal.model_prob < 0.80:
        return QualityVerdict(False, f"model_prob {signal.model_prob:.0%} < 80%")
    if signal.stake_fraction > 0.0333 + 1e-9:
        return QualityVerdict(False, f"stake {signal.stake_fraction:.4f} > 1/30")

    bks = bookmakers or []
    odds_bk = (match_detail or {}).get("oddsBk") or {}
    market_odds = _best_odds_map(
        odds_bk,
        bks,
        [
            "w1",
            "x",
            "w2",
            "dnb_1",
            "dnb_2",
            "dc_1x",
            "dc_x2",
            "total_over_25",
            "total_under_25",
            "btts_yes",
            "btts_no",
        ],
    )
    if match_detail and bks:
        from src.signal_quality import market_disagreement_reason

        disagree = market_disagreement_reason(odds_bk, bks, signal.outcome)
        if disagree:
            return QualityVerdict(False, f"против рынка: {disagree}")

    prompt = (
        "Ты стоп-кран канала «Честная ставка», не cheerleader.\n"
        "Задача: НЕ пропустить мусорный VALUE. Сомневаешься — ok=false.\n\n"
        "Обязательный отказ (ok=false), если:\n"
        f"- edge > {max_edge:.0%} (это почти всегда ошибка модели, не «подарок» БК);\n"
        "- исход спорит с явным фаворитом рынка по 1X2 / тоталу / ОЗ;\n"
        "- edge выглядит нереально жирным при коротком или длинном кэфе без здравого смысла;\n"
        "- model_prob < 0.80, edge <= 0, stake > 1/30;\n"
        "- текст поста противоречит цифрам.\n\n"
        "ok=true только если цифры согласованы, edge умеренный и нет явного спора с линией.\n\n"
        f"Матч: {signal.home_team} — {signal.away_team} | {signal.league_name}\n"
        f"Исход: {signal.outcome_label} ({signal.outcome})\n"
        f"model_prob={signal.model_prob:.4f}\n"
        f"best_odds={signal.best_odds:.3f} ({signal.best_bookmaker})\n"
        f"implied={None if implied is None else round(implied, 4)}\n"
        f"edge={edge:.4f} ({edge:.1%})\n"
        f"stake_fraction={signal.stake_fraction:.4f}\n"
        f"max_edge_allowed={max_edge}\n"
        f"сила_сезона: {json.dumps(_season_context(match_detail or {}, model_probs or {}), ensure_ascii=False)}\n"
        f"рынок (лучшие кэфы RU-БК): {json.dumps(market_odds, ensure_ascii=False)}\n\n"
        f"Текст поста:\n{signal_text}\n\n"
        "Ответь СТРОГО JSON: {\"ok\": true|false, \"summary\": \"кратко по-русски почему\"}."
    )
    try:
        raw = client.chat(
            [
                {
                    "role": "system",
                    "content": (
                        "Ты скептичный риск-контролёр ставок. "
                        "Отвечай только валидным JSON. При сомнении — ok=false."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
        )
        data = _extract_json(raw)
        # Нет явного ok → не пропускаем (скептический default).
        if "ok" not in data:
            return QualityVerdict(
                False,
                f"logic JSON без поля ok: {str(data.get('summary') or raw)[:500]}",
                raw,
            )
        ok = bool(data.get("ok"))
        summary = str(data.get("summary") or raw)[:1000]
        return QualityVerdict(ok, summary, raw)
    except Exception as exc:
        logger.warning("logic check failed (after failover if any): {}", exc)
        # Только транспорт/шлюз: канал не молчит. Явный ok=false выше уже вернул False.
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
        "Ты судья «верняка» для канала «Честная ставка».\n"
        "Верняк ≠ value. Низкий кэф сам по себе НЕ делает верняк.\n\n"
        "Верняк = явный фаворит, который заметно сильнее соперника «на голову», "
        "а не просто «неплохо смотрится».\n"
        "Хорошие признаки (нужно несколько сразу):\n"
        "- сила сезона / таблица: фаворит из верхней части, оппонент заметно ниже "
        "(большой разрыв позиций/очков), либо явный разрыв λ атаки/защиты;\n"
        "- форма/streaks не противоречат фавориту;\n"
        "- h2h может усиливать, но один h2h без сезона — мало;\n"
        "- нет серьёзных missingPlayers у фаворита;\n"
        "- линия БК в целом согласна, что это фаворит.\n\n"
        "НЕ верняк, если:\n"
        "- середняк vs середняк / равные по таблице;\n"
        "- только «неплохая форма» без явного превосходства;\n"
        "- модель и рынок смотрят в разные стороны;\n"
        "- много красных флагов (травмы ключа, провал формы).\n\n"
        "Слова «безоговорочный» не требуются — нужна ясная иерархия сил, не идеальная гарантия.\n\n"
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
