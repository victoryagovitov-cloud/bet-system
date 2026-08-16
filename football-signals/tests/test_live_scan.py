from src.live.discovery import is_inplay_status, list_inplay_matches
from src.live.live_value import evaluate_match
from src.live.session import LiveSession
from src.live.stats_parse import parse_match_statistics
from src.live.tempo_model import build_live_probs


def _stats_block(
    *,
    xg_h: float,
    xg_a: float,
    sot_h: float = 4,
    sot_a: float = 1,
    shots_h: float = 10,
    shots_a: float = 3,
    poss_h: float = 62,
    poss_a: float = 38,
) -> list[dict]:
    return [
        {
            "period": "ALL",
            "groups": [
                {
                    "groupName": "Match overview",
                    "statisticsItems": [
                        {
                            "key": "expectedGoals",
                            "homeValue": xg_h,
                            "awayValue": xg_a,
                        },
                        {
                            "key": "shotsOnGoal",
                            "homeValue": sot_h,
                            "awayValue": sot_a,
                        },
                        {
                            "key": "totalShotsOnGoal",
                            "homeValue": shots_h,
                            "awayValue": shots_a,
                        },
                        {
                            "key": "ballPossession",
                            "homeValue": poss_h,
                            "awayValue": poss_a,
                        },
                    ],
                }
            ],
        }
    ]


def _odds(total_over: float = 2.10, w1: float = 2.40) -> dict:
    return {
        "melbet": {
            "isBettingActive": True,
            "markets": {
                "total": {
                    "isLive": True,
                    "suspended": False,
                    "stakes": {
                        "over": {"lines": [{"argument": 2.5, "factor": total_over}]},
                        "under": {"lines": [{"argument": 2.5, "factor": 1.75}]},
                    },
                },
                "result": {
                    "isLive": True,
                    "stakes": {
                        "w1": {"factor": w1},
                        "x": {"factor": 3.2},
                        "w2": {"factor": 3.5},
                    },
                },
                "btts": {
                    "isLive": True,
                    "stakes": {"yes": {"factor": 1.90}, "no": {"factor": 1.90}},
                },
                "double_chance": {
                    "isLive": True,
                    "stakes": {
                        "1x": {"factor": 1.45},
                        "12": {"factor": 1.30},
                        "x2": {"factor": 1.55},
                    },
                },
            },
        }
    }


def test_parse_match_statistics_reads_xg_and_possession():
    match = {"matchStatistics": _stats_block(xg_h=1.4, xg_a=0.3)}
    stats = parse_match_statistics(match)
    assert stats is not None
    assert stats.home.xg == 1.4
    assert stats.away.xg == 0.3
    assert stats.home.possession == 62
    assert stats.has_usable_stats


def test_discovery_filters_inplay_and_whitelist():
    matches = [
        {"id": 1, "status": "inprogress", "currentMatchMinute": 33, "tournament": {"id": 999001}},
        {"id": 2, "status": "notstarted", "tournament": {"id": 17}},
        {"id": 3, "status": "finished", "tournament": {"id": 17}},
        {"id": 4, "status": "inprogress", "currentMatchMinute": 50, "tournament": {"id": 17}},
    ]

    def league_ok(tid):
        return int(tid) == 17

    rows = list_inplay_matches(matches, whitelist_only=True, league_ok=league_ok)
    assert [m["id"] for m in rows] == [4]
    assert is_inplay_status(matches[0]) is True
    assert is_inplay_status(matches[1]) is False


def test_tempo_model_skips_without_stats_and_scores_with_pressure():
    bare = {
        "id": 10,
        "status": "inprogress",
        "currentMatchMinute": 40,
        "homeScore": {"current": 0},
        "awayScore": {"current": 0},
        "homeTeam": {"id": 1, "name": "Home"},
        "awayTeam": {"id": 2, "name": "Away"},
        "tournament": {"id": 17, "name": "PL"},
        "pregame": {},
    }
    skipped = build_live_probs(bare, require_stats=True)
    assert skipped.skip_reason == "no_usable_stats"

    rich = {
        **bare,
        "matchStatistics": _stats_block(xg_h=1.6, xg_a=0.2),
        "oddsBk": _odds(),
    }
    model = build_live_probs(rich, require_stats=True)
    assert model.skip_reason is None
    assert model.probs["total_over_25"] > 0
    assert model.tempo_home >= 1.0


def test_evaluate_match_returns_live_candidate(tmp_path):
    match = {
        "id": 42,
        "status": "inprogress",
        "currentMatchMinute": 35,
        "homeScore": {"current": 0},
        "awayScore": {"current": 0},
        "homeTeam": {"id": 1, "name": "Home", "translations": {"ru": "Хозяева"}},
        "awayTeam": {"id": 2, "name": "Away", "translations": {"ru": "Гости"}},
        "tournament": {"id": 17, "name": "PL", "translations": {"ru": "АПЛ"}},
        "pregame": {},
        "matchStatistics": _stats_block(xg_h=1.8, xg_a=0.2, sot_h=6, sot_a=1),
        "oddsBk": _odds(total_over=2.40, w1=2.80),
    }
    cand, reason = evaluate_match(
        match,
        ["melbet"],
        min_model_probability=0.40,
        min_edge=0.03,
        max_edge=0.35,
        require_heuristic=True,
    )
    assert reason is None
    assert cand is not None
    assert cand.signal_kind == "live"
    assert cand.match_id == 42
    assert cand.edge >= 0.03


def test_live_session_caps_and_dedups(tmp_path):
    from src.live.live_value import LiveCandidate

    path = tmp_path / "session.json"
    session = LiveSession(path, max_signals=2)

    def cand(mid: int, edge: float) -> LiveCandidate:
        return LiveCandidate(
            match_id=mid,
            home_team="H",
            away_team="A",
            league_id=1,
            league_name="L",
            minute=40,
            score="0:0",
            outcome="total_over_25",
            outcome_label="ТБ 2.5",
            model_prob=0.7,
            best_bookmaker="melbet",
            best_odds=2.0,
            edge=edge,
            lambda_home_remain=0.8,
            lambda_away_remain=0.5,
            tempo_home=1.2,
            tempo_away=0.9,
        )

    picked = session.select([cand(1, 0.12), cand(2, 0.10), cand(3, 0.09)])
    assert [c.match_id for c in picked] == [1, 2]
    assert session.remaining_slots == 0

    session2 = LiveSession(path, max_signals=2)
    assert session2.already_seen(1)
    assert session2.select([cand(1, 0.99), cand(3, 0.50)]) == []
