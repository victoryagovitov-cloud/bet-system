from datetime import date
from unittest.mock import MagicMock

from src.llm_quality import FailoverClient, check_logic, check_lock
from src.metrics import brier_score, compute_clv
from src.llm_quality import _extract_json
from src.signal_formatter import format_daily_digest, format_signal
from src.stake_engine import calculate_lock_stake_fraction
from src.value_engine import (
    SignalCandidate,
    find_lock_candidate,
    find_signal,
    get_outcome_odds,
    odds_spread_for_outcome,
)


def _match_shell(
    *,
    home_wins: int = 8,
    away_wins: int = 1,
    draws: int = 1,
    w1_odds: float = 1.30,
    w2_odds: float = 5.0,
) -> dict:
    return {
        "id": 101,
        "dateEvent": "2026-08-20T18:00:00",
        "homeTeam": {"name": "Big Favorite"},
        "awayTeam": {"name": "Underdog FC"},
        "tournament": {"id": 1, "name": "Test League", "translations": {"ru": "Тест"}},
        "pregame": {
            "h2h": {"teamDuel": {"homeWins": home_wins, "awayWins": away_wins, "draws": draws}},
            "teamStreaks": {"general": [{"name": "Wins", "value": "5", "team": "home"}]},
            "form": None,
        },
        "oddsBk": {
            "melbet": {
                "isBettingActive": True,
                "markets": {
                    "result": {
                        "stakes": {
                            "w1": {"factor": w1_odds},
                            "w2": {"factor": w2_odds},
                            "x": {"factor": 4.5},
                        }
                    },
                    "double_chance": {
                        "stakes": {
                            "1x": {"factor": 1.12},
                            "x2": {"factor": 2.8},
                        }
                    },
                    "handicap": {
                        "stakes": {
                            "handicap_1": {"lines": [{"argument": 0.0, "factor": 1.28}]},
                            "handicap_2": {"lines": [{"argument": 0.0, "factor": 3.5}]},
                        }
                    },
                },
            }
        },
    }


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
        pending_settlement=3,
    )
    assert "Коротко по проверке" in text
    assert "Проверка прошла нормально" in text
    assert "100" in text
    assert "ждут результата" in text or "ранее данным" in text
    assert "Новых ставок сейчас нет" in text
    assert "⚠️" in text


def test_format_accounting_report():
    from src.settlement import SettleSnapshot
    from src.signal_formatter import format_accounting_report

    empty = format_accounting_report(
        SettleSnapshot(
            settled_now=0,
            pending=2,
            n=0,
            hit_rate=None,
            mean_model_prob=None,
            brier=None,
            mean_clv=None,
            by_league={},
        )
    )
    assert empty.startswith("Как сыграли наши сигналы")
    assert "рано" in empty.lower() or "нечего считать" in empty.lower()

    filled = format_accounting_report(
        SettleSnapshot(
            settled_now=1,
            voids_now=0,
            pending=4,
            n=12,
            hit_rate=0.75,
            mean_model_prob=0.84,
            brier=0.18,
            mean_clv=0.01,
            by_league={},
        )
    )
    assert "Зашло из посчитанных" in filled
    assert "режиме наблюдения" in filled


def test_lock_prefilter_accepts_dominant_favorite():
    match = _match_shell(w1_odds=1.30)
    probs = {
        "w1": 0.82,
        "x": 0.12,
        "w2": 0.06,
        "dc_1x": 0.90,
        "dc_x2": 0.18,
        "dnb_1": 0.88,
        "dnb_2": 0.12,
        "_lambda_home": 2.0,
        "_lambda_away": 0.9,
    }
    cand = find_lock_candidate(match, probs, ["melbet"])
    assert cand is not None
    assert cand.signal_kind == "lock"
    assert cand.outcome in {"w1", "dnb_1", "dc_1x"}
    assert cand.model_prob >= 0.78


def test_lock_prefilter_rejects_long_odds_underdog():
    # All favorite-side markets outside discussion corridor → no lock candidate
    match = _match_shell(w1_odds=3.35, w2_odds=1.30)
    match["oddsBk"]["melbet"]["markets"]["double_chance"]["stakes"]["1x"]["factor"] = 1.55
    match["oddsBk"]["melbet"]["markets"]["handicap"]["stakes"]["handicap_1"]["lines"][0][
        "factor"
    ] = 1.55
    probs = {
        "w1": 0.89,
        "x": 0.07,
        "w2": 0.04,
        "dc_1x": 0.92,
        "dnb_1": 0.90,
        "_lambda_home": 2.1,
        "_lambda_away": 0.8,
    }
    cand = find_lock_candidate(match, probs, ["melbet"])
    assert cand is None


def test_value_beats_lock_when_edge_positive():
    match = _match_shell(w1_odds=1.40)
    # implied ~71%, model 85% → edge > 0 value
    probs = {
        "w1": 0.85,
        "x": 0.10,
        "w2": 0.05,
        "dc_1x": 0.92,
        "dnb_1": 0.90,
        "_lambda_home": 2.0,
        "_lambda_away": 0.9,
    }
    value = find_signal(match, probs, ["melbet"], min_model_probability=0.80)
    lock = find_lock_candidate(match, probs, ["melbet"])
    assert value is not None
    assert value.signal_kind == "value"
    assert value.edge > 0
    # Both may exist as candidates; pipeline prefers value
    assert lock is not None


def test_lock_stake_fixed():
    assert abs(calculate_lock_stake_fraction(1 / 60) - (1 / 60)) < 1e-9


def test_check_lock_fail_closed_without_client():
    signal = SignalCandidate(
        match_id=1,
        home_team="A",
        away_team="B",
        league_id=1,
        league_name="L",
        kickoff=None,
        outcome="w1",
        outcome_label="П1",
        model_prob=0.85,
        best_bookmaker="melbet",
        best_odds=1.30,
        edge=0.08,
        signal_kind="lock",
    )
    v = check_lock(signal, {}, {"w1": 0.85}, client=None, enabled=True)
    assert v.ok is False


def test_check_lock_mock_reject_and_accept():
    signal = SignalCandidate(
        match_id=1,
        home_team="A",
        away_team="B",
        league_id=1,
        league_name="L",
        kickoff=None,
        outcome="w1",
        outcome_label="П1",
        model_prob=0.85,
        best_bookmaker="melbet",
        best_odds=1.30,
        edge=0.0,
        signal_kind="lock",
    )
    client = MagicMock()
    client.chat.return_value = '{"is_lock": false, "confidence": 0.9, "reasons": ["спорно"], "risks": ["форма"]}'
    rejected = check_lock(signal, _match_shell(), {"w1": 0.85, "_lambda_home": 2.0, "_lambda_away": 1.0}, client=client, enabled=True)
    assert rejected.ok is False

    client.chat.return_value = (
        '{"is_lock": true, "confidence": 0.88, "reasons": ["доминирование H2H"], "risks": []}'
    )
    accepted = check_lock(
        signal,
        _match_shell(),
        {"w1": 0.85, "_lambda_home": 2.0, "_lambda_away": 1.0},
        client=client,
        enabled=True,
        min_confidence=0.75,
    )
    assert accepted.ok is True
    assert accepted.confidence == 0.88
    assert "H2H" in accepted.summary


def test_format_lock_signal():
    s = SignalCandidate(
        match_id=1,
        home_team="A",
        away_team="B",
        league_id=1,
        league_name="L",
        kickoff="2026-08-20",
        outcome="w1",
        outcome_label="П1",
        model_prob=0.85,
        best_bookmaker="melbet",
        best_odds=1.28,
        edge=-0.01,
        stake_fraction=1 / 60,
        signal_kind="lock",
        lock_reasons=["Сильный H2H"],
        lock_confidence=0.9,
    )
    text = format_signal(s, 30000)
    assert text.startswith("ВЕРНЯК")
    assert "Сильный H2H" in text
    assert "Edge:" not in text
    assert "⚠️" in text
    assert "Размер:" in text or "Ставка:" in text


def test_format_value_has_disclaimer_footer():
    s = SignalCandidate(
        match_id=2,
        home_team="Home",
        away_team="Away",
        league_id=1,
        league_name="L",
        kickoff="2026-08-20",
        outcome="dc_1x",
        outcome_label="1X",
        model_prob=0.84,
        best_bookmaker="marathon",
        best_odds=1.27,
        edge=0.05,
        stake_fraction=0.0333,
        signal_kind="value",
    )
    text = format_signal(s, 30000)
    assert text.startswith("СТАВКА (хорошая цена)")
    assert "Запас над ценой букмекера: 5.0%" in text
    assert "ценный" not in text.lower()
    assert "value" not in text.lower()
    assert "купон" not in text.lower()
    assert "⚠️" in text
    assert "────────" in text


def test_digest_uses_plain_channel_terms():
    empty = format_daily_digest(
        target_date=date(2026, 8, 18),
        matches_with_odds=10,
        matches_in_whitelist=3,
        signals=[],
        footer_tip="День без ставки — норма.",
    )
    assert "купон" not in empty.lower()
    assert "ценный" not in empty.lower()
    assert "Новых ставок сейчас нет" in empty
    assert "слабую ставку" in empty
    assert empty.count("⚠️") == 1
    # Одна короткая фраза в подвале, не три подряд.
    assert "День без ставки — норма." in empty

    s = SignalCandidate(
        match_id=2,
        home_team="Home",
        away_team="Away",
        league_id=1,
        league_name="L",
        kickoff="2026-08-20",
        outcome="dc_1x",
        outcome_label="1X",
        model_prob=0.84,
        best_bookmaker="marathon",
        best_odds=1.27,
        edge=0.05,
        stake_fraction=0.0333,
        signal_kind="value",
    )
    filled = format_daily_digest(
        target_date=date(2026, 8, 18),
        matches_with_odds=10,
        matches_in_whitelist=3,
        signals=[s],
        footer_tip="Берегите банк и голову.",
    )
    assert "хорошая цена — 1" in filled
    assert "[хорошая цена]" in filled
    assert "ценный" not in filled.lower()
    assert "купон" not in filled.lower()
    assert filled.count("⚠️") == 1
    assert "Берегите банк и голову." in filled
    assert "Разбираем честно" not in filled


def test_rotating_tips_cycles(tmp_path):
    from src.phrase_bank import ROTATING_TIPS, RotatingTips

    path = tmp_path / "phrase_rotation.json"
    rot = RotatingTips(path)
    first = rot.next()
    second = rot.next()
    assert first in ROTATING_TIPS
    assert second in ROTATING_TIPS
    assert first != second or len(ROTATING_TIPS) == 1

    rot2 = RotatingTips(path)
    third = rot2.next()
    assert third == ROTATING_TIPS[2 % len(ROTATING_TIPS)]


def test_failover_uses_backup_on_primary_fail():
    primary = MagicMock()
    primary.label = "p"
    primary.model = "bad"
    primary.chat.side_effect = ValueError("empty")
    backup = MagicMock()
    backup.label = "f"
    backup.model = "good"
    backup.chat.return_value = '{"ok": true, "summary": "ok"}'
    client = FailoverClient(primary, backup)
    out = client.chat([{"role": "user", "content": "hi"}])
    assert "ok" in out
    backup.chat.assert_called_once()


def test_logic_fail_open_when_llm_dies():
    """Сбой шлюза не должен обнулять канал; явный ok=false по-прежнему блокирует."""
    signal = SignalCandidate(
        match_id=1,
        home_team="A",
        away_team="B",
        league_id=1,
        league_name="L",
        kickoff=None,
        outcome="w1",
        outcome_label="П1",
        model_prob=0.85,
        best_bookmaker="melbet",
        best_odds=1.30,
        edge=0.08,
        stake_fraction=0.03,
        signal_kind="value",
    )
    client = MagicMock()
    client.chat.side_effect = ValueError("empty content")
    v = check_logic(signal, "текст", client=client, enabled=True)
    assert v.ok is True
    assert "fail-open" in v.summary

    client.chat.side_effect = None
    client.chat.return_value = '{"ok": false, "summary": "edge подозрительный"}'
    blocked = check_logic(signal, "текст", client=client, enabled=True)
    assert blocked.ok is False


def test_logic_hard_blocks_fat_edge_without_llm():
    signal = SignalCandidate(
        match_id=1,
        home_team="A",
        away_team="B",
        league_id=1,
        league_name="L",
        kickoff=None,
        outcome="w1",
        outcome_label="П1",
        model_prob=0.88,
        best_bookmaker="melbet",
        best_odds=2.08,
        edge=0.35,
        stake_fraction=0.0333,
        signal_kind="value",
    )
    client = MagicMock()
    v = check_logic(signal, "VALUE…", client=client, enabled=True, max_edge=0.15)
    assert v.ok is False
    assert "жирный" in v.summary or "max" in v.summary
    client.chat.assert_not_called()


def test_logic_allows_edge_between_12_and_15_to_reach_llm():
    signal = SignalCandidate(
        match_id=1,
        home_team="A",
        away_team="B",
        league_id=1,
        league_name="L",
        kickoff=None,
        outcome="w1",
        outcome_label="П1",
        model_prob=0.88,
        best_bookmaker="melbet",
        best_odds=1.35,
        edge=0.14,
        stake_fraction=0.0333,
        signal_kind="value",
    )
    client = MagicMock()
    client.chat.return_value = '{"ok": true, "summary": "умеренный edge"}'
    v = check_logic(signal, "VALUE…", client=client, enabled=True, max_edge=0.15)
    assert v.ok is True
    client.chat.assert_called_once()


def test_logic_missing_ok_field_is_block():
    signal = SignalCandidate(
        match_id=1,
        home_team="A",
        away_team="B",
        league_id=1,
        league_name="L",
        kickoff=None,
        outcome="w1",
        outcome_label="П1",
        model_prob=0.85,
        best_bookmaker="melbet",
        best_odds=1.30,
        edge=0.08,
        stake_fraction=0.03,
        signal_kind="value",
    )
    client = MagicMock()
    client.chat.return_value = '{"summary": "всё ок"}'
    v = check_logic(signal, "текст", client=client, enabled=True)
    assert v.ok is False
