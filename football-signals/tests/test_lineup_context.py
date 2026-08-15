from src.lineup_context import (
    blocks_outcome,
    extract_missing,
    lambda_penalties,
)
from src.probability_model import compute


def _missing_item(name: str, position: str, reason: str = "Injury") -> dict:
    return {
        "player": {
            "name": name,
            "position": position,
            "translations": {"ru": name},
        },
        "type": "missing",
        "reason": {"name": reason, "translations": {"ru": reason}},
    }


def test_extract_missing_counts():
    match = {
        "homeTeam": {
            "lineup": {
                "missingPlayers": [
                    _missing_item("A", "D"),
                    _missing_item("B", "F"),
                ]
            }
        },
        "awayTeam": {"lineup": {"missingPlayers": [_missing_item("C", "G")]}},
    }
    s = extract_missing(match)
    assert s.home_count == 2
    assert s.away_count == 1
    assert s.has_key("home")
    assert s.has_key("away")


def test_lambda_penalty_soft_cap():
    match = {
        "homeTeam": {
            "lineup": {
                "missingPlayers": [
                    _missing_item("1", "F"),
                    _missing_item("2", "F"),
                    _missing_item("3", "M"),
                    _missing_item("4", "D"),
                    _missing_item("5", "G"),
                ]
            }
        },
        "awayTeam": {},
    }
    h, a = lambda_penalties(extract_missing(match))
    assert a == 0.0
    assert h < 0
    assert h >= -0.35


def test_blocks_heavy_home_absences():
    match = {
        "homeTeam": {
            "lineup": {
                "missingPlayers": [
                    _missing_item("1", "D"),
                    _missing_item("2", "M"),
                    _missing_item("3", "M"),
                ]
            }
        },
        "awayTeam": {},
    }
    s = extract_missing(match)
    assert blocks_outcome("w1", s)
    assert blocks_outcome("dnb_1", s)
    assert blocks_outcome("w2", s) is None
    assert blocks_outcome("total_over_25", s) is None


def test_blocks_key_duo():
    match = {
        "awayTeam": {
            "lineup": {
                "missingPlayers": [
                    _missing_item("GK", "G"),
                    _missing_item("ST", "F"),
                ]
            }
        },
        "homeTeam": {},
    }
    s = extract_missing(match)
    assert blocks_outcome("w2", s)
    assert blocks_outcome("w1", s) is None


def test_missing_lowers_lambda_in_model():
    base = {
        "pregame": {
            "h2h": {"teamDuel": {"homeWins": 5, "awayWins": 5, "draws": 0}},
            "teamStreaks": {"general": []},
            "form": None,
        }
    }
    with_miss = {
        **base,
        "homeTeam": {
            "lineup": {
                "missingPlayers": [
                    _missing_item("1", "F"),
                    _missing_item("2", "M"),
                ]
            }
        },
    }
    p0 = compute(base)
    p1 = compute(with_miss)
    assert p1["_lambda_home"] < p0["_lambda_home"]
    assert p1["_missing_home"] == 2.0
