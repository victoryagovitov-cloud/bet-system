from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class SignalRow(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(Integer, index=True)
    home_team: Mapped[str] = mapped_column(String(256))
    away_team: Mapped[str] = mapped_column(String(256))
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    league_name: Mapped[str] = mapped_column(String(256))
    kickoff: Mapped[str | None] = mapped_column(String(64), nullable=True)
    outcome: Mapped[str] = mapped_column(String(32))
    outcome_label: Mapped[str] = mapped_column(String(64))
    model_prob: Mapped[float] = mapped_column(Float)
    best_bookmaker: Mapped[str] = mapped_column(String(32))
    best_odds: Mapped[float] = mapped_column(Float)
    edge: Mapped[float] = mapped_column(Float)
    stake_fraction: Mapped[float] = mapped_column(Float)
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    publish_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_win: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    final_score: Mapped[str | None] = mapped_column(String(32), nullable=True)


def make_engine(database_url: str):
    return create_engine(database_url, future=True)


def make_session_factory(database_url: str):
    engine = make_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
