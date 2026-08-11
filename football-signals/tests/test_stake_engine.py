from src.stake_engine import calculate_stake_fraction


def test_kelly_table_values():
    # odds 1.30, p=0.80 → full≈13.33%, quarter≈3.33%
    q = calculate_stake_fraction(0.80, 1.30, kelly_mode="quarter", hard_cap=0.0333)
    assert abs(q - 0.0333) < 1e-3

    # odds 1.40, p=0.80 → full=30%, quarter=7.5% → cap 3.33%
    q2 = calculate_stake_fraction(0.80, 1.40, kelly_mode="quarter", hard_cap=0.0333)
    assert abs(q2 - 0.0333) < 1e-9

    # odds 1.20, p=0.80 → edge negative → 0
    assert calculate_stake_fraction(0.80, 1.20, kelly_mode="quarter") == 0.0


def test_full_kelly_raw():
    full = calculate_stake_fraction(0.80, 1.40, kelly_mode="full", hard_cap=1.0)
    assert abs(full - 0.30) < 1e-9
