from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from src.db.models import SignalRow, make_session_factory
from src.value_engine import SignalCandidate


class SignalRepository:
    def __init__(self, database_url: str):
        self._Session = make_session_factory(database_url)

    def save_signal(self, signal: SignalCandidate, publish_ref: str | None = None) -> int:
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
            published_at=datetime.utcnow(),
            publish_ref=publish_ref,
        )
        with self._Session() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
            return int(row.id)

    def unsettled(self) -> list[SignalRow]:
        with self._Session() as session:
            rows = session.scalars(
                select(SignalRow).where(SignalRow.result_win.is_(None))
            ).all()
            return list(rows)

    def mark_settled(self, signal_id: int, won: bool, final_score: str | None) -> None:
        with self._Session() as session:
            row = session.get(SignalRow, signal_id)
            if not row:
                return
            row.result_win = won
            row.final_score = final_score
            row.settled_at = datetime.utcnow()
            session.commit()
