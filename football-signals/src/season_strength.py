"""Сила сезона из турнирной таблицы API-SPORT (атака/защита → λ)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TeamSeasonStats:
    team_id: int
    matches: int
    goals_for: float
    goals_against: float
    points: float
    position: int | None = None

    @property
    def gf_pg(self) -> float:
        return self.goals_for / self.matches if self.matches > 0 else 0.0

    @property
    def ga_pg(self) -> float:
        return self.goals_against / self.matches if self.matches > 0 else 0.0


def index_standings(payload: dict | None, *, min_matches: int = 3) -> dict[int, TeamSeasonStats]:
    """
    Собирает team_id → статистика из ответа /tournament/{id}/standings.
    Если таблиц несколько — берём блок с максимальным числом строк.
    """
    if not isinstance(payload, dict):
        return {}
    blocks = payload.get("standings") or []
    if not isinstance(blocks, list) or not blocks:
        return {}

    best_rows: list[dict] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        rows = block.get("rows") or []
        if isinstance(rows, list) and len(rows) > len(best_rows):
            best_rows = rows

    out: dict[int, TeamSeasonStats] = {}
    for row in best_rows:
        if not isinstance(row, dict):
            continue
        team = row.get("team") or {}
        try:
            team_id = int(team.get("id"))
            matches = int(row.get("matches") or 0)
            gf = float(row.get("scoresFor") or 0)
            ga = float(row.get("scoresAgainst") or 0)
            pts = float(row.get("points") or 0)
        except (TypeError, ValueError):
            continue
        if matches < min_matches:
            continue
        pos = row.get("position")
        try:
            position = int(pos) if pos is not None else None
        except (TypeError, ValueError):
            position = None
        out[team_id] = TeamSeasonStats(
            team_id=team_id,
            matches=matches,
            goals_for=gf,
            goals_against=ga,
            points=pts,
            position=position,
        )
    return out


def estimate_lambdas_from_season(
    home_id: int | None,
    away_id: int | None,
    by_team: dict[int, TeamSeasonStats],
    *,
    home_advantage: float = 1.08,
) -> tuple[float, float] | None:
    """
    Классическая схема attack×defense относительно средней лиги.
    Без кэфов БК. None — если данных мало.
    """
    if home_id is None or away_id is None:
        return None
    home = by_team.get(int(home_id))
    away = by_team.get(int(away_id))
    if home is None or away is None:
        return None
    if len(by_team) < 4:
        return None

    avg_gf = sum(t.gf_pg for t in by_team.values()) / len(by_team)
    avg_ga = sum(t.ga_pg for t in by_team.values()) / len(by_team)
    if avg_gf <= 0.05 or avg_ga <= 0.05:
        return None

    att_h = home.gf_pg / avg_gf
    def_h = home.ga_pg / avg_ga
    att_a = away.gf_pg / avg_gf
    def_a = away.ga_pg / avg_ga

    # База голов — среднее забитых в лиге (≈ среднее за матч на команду)
    lambda_home = att_h * def_a * avg_gf * home_advantage
    lambda_away = att_a * def_h * avg_gf
    return float(lambda_home), float(lambda_away)


def team_id_from_match(match: dict, side: str) -> int | None:
    key = "homeTeam" if side == "home" else "awayTeam"
    team = match.get(key) or {}
    try:
        return int(team.get("id"))
    except (TypeError, ValueError):
        return None


def attach_season_stats(match: dict, by_team: dict[int, TeamSeasonStats]) -> dict:
    """Кладёт индекс силы сезона в match для probability_model (копия не нужна)."""
    match["_season_by_team"] = by_team
    return match
