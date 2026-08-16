from src.signal_quality import market_disagreement_reason, quality_skip_reason
from src.value_engine import find_signal


def _odds(w1=1.3, w2=5.0, over=1.5, under=2.5, btts_yes=1.7, btts_no=2.1):
    return {
        "melbet": {
            "isBettingActive": True,
            "markets": {
                "result": {
                    "stakes": {
                        "w1": {"factor": w1},
                        "x": {"factor": 4.0},
                        "w2": {"factor": w2},
                    }
                },
                "total": {
                    "stakes": {
                        "over": {"lines": [{"argument": 2.5, "factor": over}]},
                        "under": {"lines": [{"argument": 2.5, "factor": under}]},
                    }
                },
                "btts": {"stakes": {"yes": {"factor": btts_yes}, "no": {"factor": btts_no}}},
                "handicap": {
                    "stakes": {
                        "handicap_1": {"lines": [{"argument": 0.0, "factor": 1.25}]},
                        "handicap_2": {"lines": [{"argument": 0.0, "factor": 3.5}]},
                    }
                },
            },
        }
    }


def test_rejects_edge_above_max():
    match = {
        "id": 1,
        "tournament": {"id": 1, "name": "L"},
        "homeTeam": {"name": "A"},
        "awayTeam": {"name": "B"},
        "oddsBk": _odds(w1=2.5, w2=1.5),  # market favors away
    }
    # model loves home DNB with huge edge vs long odds — should die on market + edge
    probs = {
        "dnb_1": 0.88,
        "w1": 0.70,
        "w2": 0.10,
        "x": 0.20,
        "_lambda_home": 2.0,
        "_lambda_away": 0.8,
    }
    assert find_signal(match, probs, ["melbet"], 0.80, min_edge=0.02, max_edge=0.12) is None


def test_accepts_aligned_moderate_edge():
    match = {
        "id": 2,
        "tournament": {"id": 1, "name": "L"},
        "homeTeam": {"name": "A"},
        "awayTeam": {"name": "B"},
        "oddsBk": _odds(w1=1.30, w2=5.0),
    }
    probs = {
        "w1": 0.85,
        "x": 0.10,
        "w2": 0.05,
        "_lambda_home": 2.0,
        "_lambda_away": 0.9,
    }
    sig = find_signal(match, probs, ["melbet"], 0.80, min_edge=0.02, max_edge=0.12)
    assert sig is not None
    assert sig.outcome == "w1"
    assert sig.edge <= 0.12


def test_market_disagrees_on_under_when_over_favorite():
    odds = _odds(over=1.50, under=2.50)
    reason = market_disagreement_reason(odds, ["melbet"], "total_under_25")
    assert reason is not None


def test_lambda_floor_blocks_btts():
    skip = quality_skip_reason(
        _odds(),
        ["melbet"],
        "btts_no",
        0.81,
        2.02,
        min_edge=0.02,
        max_edge=0.50,
        model_probs={"_lambda_home": 2.0, "_lambda_away": 0.25},
    )
    assert skip and "floor" in skip
