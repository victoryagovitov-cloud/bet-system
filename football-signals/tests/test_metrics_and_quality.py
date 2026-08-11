from src.llm_quality import _extract_json
from src.metrics import brier_score, compute_clv
from src.value_engine import odds_spread_for_outcome


def test_extract_json_from_fenced():
    raw = 'Вот ответ:\n{"ok": false, "summary": "травма вратаря"}\n'
    data = _extract_json(raw)
    assert data["ok"] is False
    assert "травма" in data["summary"]


def test_clv_positive_when_publish_better_than_close():
    # publish 1.40, close 1.30 → took better price
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
