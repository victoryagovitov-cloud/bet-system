from datetime import date

from src.llm_quality import _extract_json
from src.metrics import brier_score, compute_clv
from src.signal_formatter import format_daily_digest
from src.value_engine import get_outcome_odds, odds_spread_for_outcome


def test_extract_json_from_fenced():
    raw = 'Вот ответ:\n{"ok": false, "summary": "травма вратаря"}\n'
    data = _extract_json(raw)
    assert data["ok"] is False
    assert "травма" in data["summary"]


def test_clv_positive_when_publish_better_than_close():
    clv = compute_clv(1.40, 1.30)
    assert clv > 0


def test_brier_perfect():
    class R:
        def __init__(self, p, y):
            self.model_prob = p
            self.result_win = y

    rows = [R(1.0, True), R(0.0, False)]
    assert abs(brier_score(rows) - 0.0) < 1e-12


def test_odds_spread():
    odds_bk = {
        "melbet": {"isBettingActive": True, "markets": {"result": {"stakes": {"w1": {"factor": 1.2}}}}},
        "pari": {"isBettingActive": True, "markets": {"result": {"stakes": {"w1": {"factor": 2.0}}}}},
    }
    lo, hi, spread = odds_spread_for_outcome(odds_bk, ["melbet", "pari"], "w1")
    assert lo == 1.2 and hi == 2.0 and abs(spread - 0.8) < 1e-9


def test_total_line_2_5_parsing():
    odds_bk = {
        "melbet": {
            "isBettingActive": True,
            "markets": {
                "total": {
                    "stakes": {
                        "over": {
                            "lines": [
                                {"argument": 1.5, "factor": 1.3},
                                {"argument": 2.5, "factor": 1.91},
                            ]
                        }
                    }
                }
            },
        }
    }
    assert get_outcome_odds(odds_bk, "melbet", "total_over_25") == 1.91


def test_daily_digest_zero_signals():
    text = format_daily_digest(
        target_date=date(2026, 8, 12),
        matches_with_odds=100,
        matches_in_whitelist=8,
        signals=[],
    )
    assert "Сигналов на ставку сегодня нет" in text
    assert "100" in text
