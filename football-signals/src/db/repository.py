from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from src.db.models import SignalRow, make_session_factory
from src.value_engine import SignalCandidate


class SignalRepository:
    def __init__(self, database_url: str):
        self._Session = make_session_factory(database_url)

    def get_by_match_outcome(self, match_id: int, outcome: str) -> SignalRow | None:
        with self._Session() as session:
            row = session.scalars(
                select(SignalRow).where(
                    SignalRow.match_id == match_id,
                    SignalRow.outcome == outcome,
                )
            ).first()
            if row is None:
                return None
            session.expunge(row)
            return row

    def save_signal(
        self,
        signal: SignalCandidate,
        *,
        publish_ref: str | None = None,
        status: str = "published",
        odds_min: float | None = None,
        odds_max: float | None = None,
        odds_spread: float | None = None,
        odds_spread_anomaly: bool = False,
        news_check_ok: bool | None = None,
        news_check_summary: str | None = None,
        logic_check_ok: bool | None = None,
        logic_check_summary: str | None = None,
    ) -> int:
        row = SignalRow(
            match_id=signal.match_id,
            home_team=signal.home_team,
            away_team=signal.away_team,
            league_id=signal.league_id,
            league_name=signal.league_name,
            kickoff=signal.kickoff,
            outcome=signal.outcome,
            outcome_label=signal.outcome_label,
            model_prob=signal.model_prob,
            best_bookmaker=signal.best_bookmaker,
            best_odds=signal.best_odds,
            edge=signal.edge,
            stake_fraction=signal.stake_fraction,
            signal_kind=getattr(signal, "signal_kind", None) or "value",
            status=status,
            # published_at NOT NULL в старой SQLite-схеме — всегда пишем timestamp
            published_at=datetime.utcnow(),
            publish_ref=publish_ref,
            odds_min=odds_min,
            odds_max=odds_max,
            odds_spread=odds_spread,
            odds_spread_anomaly=odds_spread_anomaly,
            news_check_ok=news_check_ok,
            news_check_summary=news_check_summary,
            logic_check_ok=logic_check_ok,
            logic_check_summary=logic_check_summary,
        )
        with self._Session() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
            return int(row.id)

    def note_odds_improvement(
        self, match_id: int, outcome: str, new_odds: float, new_bookmaker: str
    ) -> None:
        """Log-only for MVP: update best_odds if improved, do not re-publish."""
        with self._Session() as session:
            row = session.scalars(
                select(SignalRow).where(
                    SignalRow.match_id == match_id,
                    SignalRow.outcome == outcome,
                )
            ).first()
            if not row:
                return
            if new_odds > (row.best_odds or 0):
                row.best_odds = new_odds
                row.best_bookmaker = new_bookmaker
                session.commit()

    def update_status(self, signal_id: int, status: str, *, note: str | None = None) -> None:
        with self._Session() as session:
            row = session.get(SignalRow, signal_id)
            if not row:
                return
            row.status = status
            if note:
                prev = row.logic_check_summary or ""
                row.logic_check_summary = (prev + " | " if prev else "") + note
            session.commit()

    def list_published_since(self, since: datetime) -> list[SignalRow]:
        with self._Session() as session:
            rows = session.scalars(
                select(SignalRow).where(
                    SignalRow.status == "published",
                    SignalRow.published_at.is_not(None),
                    SignalRow.published_at >= since,
                )
            ).all()
            for row in rows:
                session.expunge(row)
            return list(rows)

    def unsettled(self) -> list[SignalRow]:
        with self._Session() as session:
            rows = session.scalars(
                select(SignalRow).where(
                    SignalRow.settled_at.is_(None),
                    SignalRow.status == "published",
                )
            ).all()
            for row in rows:
                session.expunge(row)
            return list(rows)

    def mark_settled(
        self,
        signal_id: int,
        won: bool | None,
        final_score: str | None,
        *,
        closing_odds: float | None = None,
        closing_bookmaker: str | None = None,
        clv: float | None = None,
    ) -> None:
        """won=True/False for graded bets; won=None for void/push (e.g. DNB draw)."""
        with self._Session() as session:
            row = session.get(SignalRow, signal_id)
            if not row:
                return
            row.result_win = won
            row.final_score = final_score
            row.settled_at = datetime.utcnow()
            if closing_odds is not None:
                row.closing_odds = closing_odds
            if closing_bookmaker is not None:
                row.closing_bookmaker = closing_bookmaker
            if clv is not None:
                row.clv = clv
            session.commit()

    def settled_published(self) -> list[SignalRow]:
        with self._Session() as session:
            rows = session.scalars(
                select(SignalRow).where(
                    SignalRow.status == "published",
                    SignalRow.result_win.is_not(None),
                )
            ).all()
            for row in rows:
                session.expunge(row)
            return list(rows)
