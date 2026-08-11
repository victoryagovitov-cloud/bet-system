from src.value_engine import find_signal


def test_picks_max_odds_and_positive_edge():
    match = {
        "id": 1,
        "dateEvent": "2026-08-12T19:00:00+00:00",
        "tournament": {"id": 17, "name": "Premier League", "translations": {"ru": "АПЛ"}},
        "homeTeam": {"name": "A", "translations": {"ru": "Хозяева"}},
        "awayTeam": {"name": "B", "translations": {"ru": "Гости"}},
        "oddsBk": {
            "melbet": {
                "isBettingActive": True,
                "markets": {"result": {"stakes": {"w1": {"factor": 1.20}, "x": {"factor": 5.0}, "w2": {"factor": 10.0}}}},
            },
            "pari": {
                "isBettingActive": True,
                "markets": {"result": {"stakes": {"w1": {"factor": 1.35}, "x": {"factor": 5.0}, "w2": {"factor": 10.0}}}},
            },
            "marathon": {"isBettingActive": False, "markets": {}},
            "betboom": {
                "isBettingActive": True,
                "markets": {"result": {"stakes": {"w1": {"factor": 1.30}, "x": {"factor": 5.0}, "w2": {"factor": 10.0}}}},
            },
        },
    }
    model_probs = {"w1": 0.85, "x": 0.10, "w2": 0.05}
    signal = find_signal(match, model_probs, ["marathon", "melbet", "betboom", "pari"], 0.80)
    assert signal is not None
    assert signal.outcome == "w1"
    assert signal.best_bookmaker == "pari"
    assert signal.best_odds == 1.35
    assert signal.edge > 0


def test_no_signal_when_edge_non_positive():
    match = {
        "id": 2,
        "tournament": {"id": 17, "name": "PL"},
        "homeTeam": {"name": "A"},
        "awayTeam": {"name": "B"},
        "oddsBk": {
            "melbet": {
                "isBettingActive": True,
                "markets": {"result": {"stakes": {"w1": {"factor": 1.10}}}},
            }
        },
    }
    # implied 1/1.10 ≈ 0.909 > 0.80 → edge negative
    signal = find_signal(match, {"w1": 0.80, "x": 0.1, "w2": 0.1}, ["melbet"], 0.80)
    assert signal is None
