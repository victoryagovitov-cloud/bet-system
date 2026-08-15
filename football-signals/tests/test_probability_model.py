from src.probability_model import compute
from src.season_strength import (
    TeamSeasonStats,
    estimate_lambdas_from_season,
    index_standings,
)


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


def test_form_boosts_attack():
    weak = compute(_fake_match(home_wins=5, away_wins=5, draws=0))
    strong = compute(
        {
            "pregame": {
                "h2h": {"teamDuel": {"homeWins": 5, "awayWins": 5, "draws": 0}},
                "teamStreaks": {"general": []},
                "form": {"home": "WWWWW", "away": "LLLLL"},
            }
        }
    )
    assert strong["_lambda_home"] > weak["_lambda_home"]
    assert strong["_lambda_away"] < weak["_lambda_away"]


def test_api_form_list_shape():
    m = {
        "homeTeam": {"id": 1},
        "awayTeam": {"id": 2},
        "pregame": {
            "h2h": {"teamDuel": {"homeWins": 1, "awayWins": 1, "draws": 1}},
            "teamStreaks": {"general": []},
            "form": {
                "homeTeam": {"position": 1, "form": ["W", "W", "W", "W"]},
                "awayTeam": {"position": 10, "form": ["L", "L", "L", "L"]},
            },
        },
    }
    probs = compute(m)
    assert probs["_lambda_home"] > probs["_lambda_away"]


def test_season_strength_from_standings():
    payload = {
        "standings": [
            {
                "name": "League",
                "rows": [
                    {
                        "position": 1,
                        "team": {"id": 10},
                        "matches": 10,
                        "scoresFor": 25,
                        "scoresAgainst": 8,
                        "points": 24,
                    },
                    {
                        "position": 2,
                        "team": {"id": 20},
                        "matches": 10,
                        "scoresFor": 18,
                        "scoresAgainst": 12,
                        "points": 18,
                    },
                    {
                        "position": 3,
                        "team": {"id": 30},
                        "matches": 10,
                        "scoresFor": 12,
                        "scoresAgainst": 15,
                        "points": 12,
                    },
                    {
                        "position": 4,
                        "team": {"id": 40},
                        "matches": 10,
                        "scoresFor": 8,
                        "scoresAgainst": 22,
                        "points": 6,
                    },
                ],
            }
        ]
    }
    by_team = index_standings(payload)
    assert 10 in by_team and 40 in by_team
    pair = estimate_lambdas_from_season(10, 40, by_team)
    assert pair is not None
    lh, la = pair
    assert lh > la

    # Without season ≈ equal h2h; with season strong home should be clearer
    base = {
        "homeTeam": {"id": 10},
        "awayTeam": {"id": 40},
        "pregame": {
            "h2h": {"teamDuel": {"homeWins": 1, "awayWins": 1, "draws": 1}},
            "teamStreaks": {"general": []},
            "form": None,
        },
    }
    without = compute(dict(base))
    with_season = compute({**base, "_season_by_team": by_team})
    assert with_season["_used_season_strength"] == 1.0
    assert without["_used_season_strength"] == 0.0
    assert with_season["w1"] > without["w1"]


def test_totals_and_dnb_present():
    probs = compute(_fake_match(home_wins=10, away_wins=1, draws=1))
    assert "total_over_25" in probs
    assert "total_under_25" in probs
    assert abs(probs["total_over_25"] + probs["total_under_25"] - 1.0) < 1e-9
    assert abs(probs["dnb_1"] + probs["dnb_2"] - 1.0) < 1e-9
    assert probs["dnb_1"] > probs["dnb_2"]
