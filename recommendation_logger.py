from __future__ import annotations

import csv
import math
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DATA_DIR = Path("data")
LOG_FILE = DATA_DIR / "recommendations_log.csv"

CSV_HEADER = [
    "timestamp_msk",
    "sport",
    "telegram_message_id",
    "slug",
    "country",
    "tournament",
    "home_team",
    "away_team",
    "score",
    "minute_display",
    "minute_numeric",
    "bet_side",
    "leader_team",
    "coefficient",
    "probability_percent",
    "dominance_score",
    "xg_home",
    "xg_away",
    "shots_on_target_home",
    "shots_on_target_away",
    "shots_total_home",
    "shots_total_away",
    "possession_home",
    "possession_away",
    "tennis_points_home",
    "tennis_points_away",
    "tennis_breaks_home",
    "tennis_breaks_away",
    "tennis_aces_home",
    "tennis_aces_away",
    "tennis_double_faults_home",
    "tennis_double_faults_away",
    "handball_projected_total",
    "handball_total_recommendation",
    "placed",
]


def _ensure_log_file() -> None:
    if not LOG_FILE.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            writer.writerow(CSV_HEADER)


def _extract_value(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


def _format_float(value: Optional[float], precision: int = 2) -> str:
    if value is None:
        return ""
    try:
        numeric = float(value)
        if math.isnan(numeric):
            return ""
        return f"{numeric:.{precision}f}"
    except (TypeError, ValueError):
        return ""


def _format_int(value: Optional[float]) -> str:
    if value is None:
        return ""
    try:
        numeric = float(value)
        if math.isnan(numeric):
            return ""
        return str(int(round(numeric)))
    except (TypeError, ValueError):
        return ""


def _prepare_row(
    match: Dict[str, Any],
    generated_at: datetime,
    message_id: Optional[int],
) -> List[str]:
    teams = match.get("teams") or ["", ""]
    home = teams[0] if len(teams) > 0 else ""
    away = teams[1] if len(teams) > 1 else ""
    leader_index = match.get("leader_index", 0)
    leader_team = teams[leader_index] if len(teams) > leader_index else ""
    bet_side = "П1" if leader_index == 0 else "П2"

    odds_info = match.get("odds_info")
    if isinstance(odds_info, dict):
        coefficient = odds_info.get("value") or odds_info.get("value", None)
    else:
        coefficient = getattr(odds_info, "value", None)

    probability = match.get("estimated_probability")

    sport = match.get("sport", "football")

    xg_home = xg_away = sot_home = sot_away = shots_home = shots_away = poss_home = poss_away = None
    tennis_points_home = tennis_points_away = ""
    tennis_breaks_home = tennis_breaks_away = ""
    tennis_aces_home = tennis_aces_away = ""
    tennis_df_home = tennis_df_away = ""
    handball_projected_total = ""
    handball_total_recommendation = ""

    if sport == "tennis":
        points = match.get("points") or (None, None)
        tennis_points_home = _format_int(points[0])
        tennis_points_away = _format_int(points[1])

        breaks = match.get("breakpoints_won") or (None, None)
        total_breaks = match.get("total_breakpoints") or (None, None)
        if breaks[0] is not None:
            if total_breaks[0] is not None:
                tennis_breaks_home = f"{_format_int(breaks[0])}/{_format_int(total_breaks[0])}"
            else:
                tennis_breaks_home = _format_int(breaks[0])
        if breaks[1] is not None:
            if total_breaks[1] is not None:
                tennis_breaks_away = f"{_format_int(breaks[1])}/{_format_int(total_breaks[1])}"
            else:
                tennis_breaks_away = _format_int(breaks[1])

        aces = match.get("aces") or (None, None)
        tennis_aces_home = _format_int(aces[0])
        tennis_aces_away = _format_int(aces[1])

        double_faults = match.get("double_faults") or (None, None)
        tennis_df_home = _format_int(double_faults[0])
        tennis_df_away = _format_int(double_faults[1])
    elif sport == "tennis":
        xg_home, xg_away = match.get("xg", (None, None))
        sot_home, sot_away = match.get("shots_on_target", (None, None))
        shots_home, shots_away = match.get("shots_total", (None, None))
        poss_home, poss_away = match.get("possession", (None, None))
    else:
        total_forecast = match.get("projected_total")
        if total_forecast is not None:
            handball_projected_total = f"{float(total_forecast):.1f}"
        recommendation = match.get("total_recommendation")
        if recommendation:
            handball_total_recommendation = (
                f"{recommendation.get('label')} {recommendation.get('value')}"
            )

    return [
        generated_at.strftime("%Y-%m-%d %H:%M:%S"),
        sport,
        str(message_id or ""),
        str(match.get("slug", "")),
        str(match.get("country", "")),
        str(match.get("tournament", "")),
        str(home),
        str(away),
        str(match.get("score", "")),
        str(match.get("minute", "")),
        str(match.get("minute_numeric", "")),
        bet_side,
        str(leader_team),
        _format_float(coefficient),
        str(probability or ""),
        _format_float(match.get("dominance_score"), precision=3),
        _format_float(xg_home),
        _format_float(xg_away),
        _format_float(sot_home, precision=1),
        _format_float(sot_away, precision=1),
        _format_float(shots_home, precision=1),
        _format_float(shots_away, precision=1),
        _format_float(poss_home, precision=1),
        _format_float(poss_away, precision=1),
        tennis_points_home,
        tennis_points_away,
        tennis_breaks_home,
        tennis_breaks_away,
        tennis_aces_home,
        tennis_aces_away,
        tennis_df_home,
        tennis_df_away,
        handball_projected_total,
        handball_total_recommendation,
        "0",
    ]


def log_recommendations(
    matches: Iterable[Dict[str, Any]],
    generated_at: datetime,
    message_id: Optional[int],
) -> None:
    matches = list(matches)
    if not matches:
        return

    _ensure_log_file()

    with LOG_FILE.open("a", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        for match in matches:
            row = _prepare_row(match, generated_at, message_id)
            writer.writerow(row)

