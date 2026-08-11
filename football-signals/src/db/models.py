from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class SignalRow(Base):
    __tablename__ = "signals"
    __table_args__ = (
        UniqueConstraint("match_id", "outcome", name="uq_signals_match_outcome"),
    )

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
    # published | blocked_news | blocked_logic | skipped_dup
    status: Mapped[str] = mapped_column(String(32), default="published")
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    publish_ref: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Bookmaker line snapshot at publish time
    odds_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    odds_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    odds_spread: Mapped[float | None] = mapped_column(Float, nullable=True)
    odds_spread_anomaly: Mapped[bool] = mapped_column(Boolean, default=False)

    # Closing line (captured near kickoff / at settle)
    closing_odds: Mapped[float | None] = mapped_column(Float, nullable=True)
    closing_bookmaker: Mapped[str | None] = mapped_column(String(32), nullable=True)
    clv: Mapped[float | None] = mapped_column(Float, nullable=True)  # publish_odds - closing? or (1/close - 1/pub)

    # LLM quality gate
    news_check_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    news_check_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    logic_check_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    logic_check_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    result_win: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    final_score: Mapped[str | None] = mapped_column(String(32), nullable=True)


def _ensure_sqlite_columns(engine) -> None:
    """Additive migrations for SQLite (create_all does not ALTER)."""
    if not str(engine.url).startswith("sqlite"):
        return
    with engine.begin() as conn:
        cols = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(signals)")).fetchall()
        }
        wanted = {
            "status": "VARCHAR(32) DEFAULT 'published'",
            "odds_min": "FLOAT",
            "odds_max": "FLOAT",
            "odds_spread": "FLOAT",
            "odds_spread_anomaly": "BOOLEAN DEFAULT 0",
            "closing_odds": "FLOAT",
            "closing_bookmaker": "VARCHAR(32)",
            "clv": "FLOAT",
            "news_check_ok": "BOOLEAN",
            "news_check_summary": "TEXT",
            "logic_check_ok": "BOOLEAN",
            "logic_check_summary": "TEXT",
        }
        for name, ddl in wanted.items():
            if name not in cols:
                conn.execute(text(f"ALTER TABLE signals ADD COLUMN {name} {ddl}"))
        # unique index for dedup (ignore if duplicates already exist — manual cleanup)
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_signals_match_outcome "
                "ON signals(match_id, outcome)"
            )
        )


def make_engine(database_url: str):
    return create_engine(database_url, future=True)


def make_session_factory(database_url: str):
    engine = make_engine(database_url)
    Base.metadata.create_all(engine)
    _ensure_sqlite_columns(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
