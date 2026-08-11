from pathlib import Path

from src.db.repository import SignalRepository
from src.value_engine import SignalCandidate


def _sig(match_id=1, outcome="w1", odds=1.4):
    return SignalCandidate(
        match_id=match_id,
        home_team="A",
        away_team="B",
        league_id=17,
        league_name="PL",
        kickoff="2026-08-15",
        outcome=outcome,
        outcome_label="П1",
        model_prob=0.85,
        best_bookmaker="melbet",
        best_odds=odds,
        edge=0.05,
        stake_fraction=0.03,
    )


def test_dedup_unique_match_outcome(tmp_path: Path):
    db = tmp_path / "t.db"
    repo = SignalRepository(f"sqlite:///{db.as_posix()}")
    repo.save_signal(_sig(odds=1.30), status="published")
    existing = repo.get_by_match_outcome(1, "w1")
    assert existing is not None
    assert existing.best_odds == 1.30
    repo.note_odds_improvement(1, "w1", 1.45, "pari")
    updated = repo.get_by_match_outcome(1, "w1")
    assert updated.best_odds == 1.45
    assert updated.best_bookmaker == "pari"
