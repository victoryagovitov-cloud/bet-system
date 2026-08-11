from src.probability_model import compute


def _fake_match(home_wins=8, away_wins=2, draws=0, streaks=None):
    return {
        "pregame": {
            "h2h": {"teamDuel": {"homeWins": home_wins, "awayWins": away_wins, "draws": draws}},
            "teamStreaks": {"general": streaks or []},
            "form": None,
        }
    }


def test_probs_sum_to_one():
    probs = compute(_fake_match())
    s = probs["w1"] + probs["x"] + probs["w2"]
    assert abs(s - 1.0) < 1e-9


def test_deterministic():
    m = _fake_match()
    assert compute(m)["w1"] == compute(m)["w1"]


def test_home_favorite_from_h2h():
    probs = compute(_fake_match(home_wins=10, away_wins=1, draws=1))
    assert probs["w1"] > probs["w2"]


def test_totals_and_dnb_present():
    probs = compute(_fake_match(home_wins=10, away_wins=1, draws=1))
    assert "total_over_25" in probs
    assert "total_under_25" in probs
    assert abs(probs["total_over_25"] + probs["total_under_25"] - 1.0) < 1e-9
    assert abs(probs["dnb_1"] + probs["dnb_2"] - 1.0) < 1e-9
    assert probs["dnb_1"] > probs["dnb_2"]
