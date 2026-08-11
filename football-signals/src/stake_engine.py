from __future__ import annotations


def calculate_stake_fraction(
    model_prob: float,
    odds: float,
    kelly_mode: str = "quarter",
    hard_cap: float = 0.0333,
) -> float:
    """
    Kelly: f* = (b*p - q) / b, b=odds-1, q=1-p
    Возвращает долю банка после kelly_mode и hard_cap.
    """
    if odds <= 1.0:
        return 0.0
    if model_prob <= 0 or model_prob >= 1:
        return 0.0

    b = odds - 1.0
    q = 1.0 - model_prob
    full_kelly = (b * model_prob - q) / b
    if full_kelly <= 0:
        return 0.0

    mode = (kelly_mode or "quarter").lower()
    if mode == "half":
        kelly = full_kelly / 2.0
    elif mode == "full":
        kelly = full_kelly
    else:
        kelly = full_kelly / 4.0

    return float(min(kelly, hard_cap))
