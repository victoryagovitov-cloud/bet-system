"""Evening live session: hard cap + match dedup (local JSON, no publish)."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from src.live.live_value import LiveCandidate

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SESSION_PATH = ROOT / "data" / "_live_session.json"


def _jsonable(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(x) for x in obj]
    return obj


class LiveSession:
    """
    Tracks which match_ids already produced a live candidate tonight.
    Caps how many signals a manual evening session may emit.
    """

    def __init__(
        self,
        path: Path | None = None,
        *,
        max_signals: int = 2,
        day: date | None = None,
    ):
        self.path = path or DEFAULT_SESSION_PATH
        self.max_signals = max(1, int(max_signals))
        self.day = (day or date.today()).isoformat()
        self._seen_match_ids: set[int] = set()
        self._emitted: list[dict] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if str(raw.get("day") or "") != self.day:
            return
        for mid in raw.get("seen_match_ids") or []:
            try:
                self._seen_match_ids.add(int(mid))
            except (TypeError, ValueError):
                continue
        emitted = raw.get("emitted") or []
        if isinstance(emitted, list):
            self._emitted = [e for e in emitted if isinstance(e, dict)]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "day": self.day,
            "max_signals": self.max_signals,
            "seen_match_ids": sorted(self._seen_match_ids),
            "emitted": self._emitted,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @property
    def remaining_slots(self) -> int:
        return max(0, self.max_signals - len(self._emitted))

    @property
    def emitted_count(self) -> int:
        return len(self._emitted)

    def already_seen(self, match_id: int) -> bool:
        return int(match_id) in self._seen_match_ids

    def select(self, candidates: Iterable[LiveCandidate]) -> list[LiveCandidate]:
        """
        Keep unseen matches, sort by edge, fill remaining evening slots.
        Marks selected matches as seen and persists session file.
        """
        if self.remaining_slots <= 0:
            return []
        fresh = [c for c in candidates if not self.already_seen(c.match_id)]
        fresh.sort(key=lambda c: c.edge, reverse=True)
        picked = fresh[: self.remaining_slots]
        for c in picked:
            self._seen_match_ids.add(int(c.match_id))
            row = _jsonable(c)
            row["selected_at"] = datetime.now(timezone.utc).isoformat()
            self._emitted.append(row)
        if picked:
            self.save()
        return picked

    def reset(self) -> None:
        self._seen_match_ids.clear()
        self._emitted.clear()
        if self.path.exists():
            self.path.unlink()
