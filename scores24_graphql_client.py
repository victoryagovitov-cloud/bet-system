import json
from typing import Any, Dict, List, Optional

import requests
import urllib3

urllib3.disable_warnings()  # Suppress InsecureRequestWarning for verify=False requests


GRAPHQL_URL = "https://scores24.live/graphql"

MATCH_LIST_QUERY = """
query LiveMatches($sport: String!, $first: Int, $after: String) {
  MatchList(sport_slug: $sport, live: true, first: $first, after: $after) {
    edges {
      node {
        slug
        minute
        match_date
        tournament_name
        category_name
        league_slug
        status { code }
        teams {
          name
        }
        game_score
        game_state {
          home_score
          away_score
        }
        country {
          name
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""


MATCH_STATS_QUERY = """
query MatchStats($slug: String!, $sport: String!) {
  Match(slug: $slug, sport_slug: $sport, lang: "ru") {
    slug
    minute
    match_date
    tournament_name
    category_name
    status { code }
    teams {
      name
      position
    }
    game_state {
      home_score
      away_score
    }
    game_score
    result_score
    result_scores {
      type
      value
      home_tiebreak_score
      away_tiebreak_score
    }
    statistic {
      periods {
        type
        groups {
          type
          items {
            type
            name
            team1_value
            team2_value
          }
        }
      }
    }
    standings {
      team {
        name
      }
      position_total
      position_home
      position_away
    }
    country {
      name
    }
    unique_tournament {
      name
    }
  }
}
"""

MATCH_ODDS_QUERY = """
query MatchOdds($slug: String!, $market: String, $limit: Int, $marketLimit: Int, $sport: String!) {
  MatchTopOdds(
    sport_slug: $sport
    slug: $slug
    market: $market
    limit: $limit
    market_limit: $marketLimit
  ) {
    market
    topRates {
      name
      values {
        outcome
        outcome_value
        value
        bookmaker {
          name
        }
      }
    }
  }
}
"""


def _post(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
  """Выполняет GraphQL запрос с обработкой ошибок и таймаутом"""
  try:
    response = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        timeout=30,  # Увеличен таймаут с 20 до 30 секунд
        verify=False,
    )
    response.raise_for_status()
    payload = response.json()
    if "errors" in payload:
      raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload.get("data", {})
  except requests.exceptions.Timeout:
    raise RuntimeError(f"GraphQL request timeout after 30 seconds")
  except requests.exceptions.ConnectionError as e:
    raise RuntimeError(f"GraphQL connection error: {e}")
  except requests.exceptions.RequestException as e:
    raise RuntimeError(f"GraphQL request error: {e}")
  except (ValueError, KeyError) as e:
    raise RuntimeError(f"GraphQL response parsing error: {e}")


def fetch_live_matches(limit: int = 50, sport: str = "soccer") -> List[Dict[str, Any]]:
  """Получает список live матчей с обработкой ошибок"""
  try:
    matches: List[Dict[str, Any]] = []
    first = min(limit, 100)
    total_collected = 0
    cursor: Optional[str] = None

    while total_collected < limit:
      remaining = limit - total_collected
      batch_size = min(first, remaining)
      variables = {"sport": sport, "first": batch_size, "after": cursor}
      data = _post(MATCH_LIST_QUERY, variables)
      connection = data.get("MatchList") or {}
      edges = connection.get("edges") or []
      for edge in edges:
        node = edge.get("node")
        if node:
          matches.append(node)
          total_collected += 1
          if total_collected >= limit:
            break
      page_info = connection.get("pageInfo") or {}
      if not page_info.get("hasNextPage"):
        break
      cursor = page_info.get("endCursor")
      if cursor is None:
        break

    return matches
  except Exception as e:
    # Логируем ошибку, но возвращаем пустой список вместо падения системы
    print(f"ERROR in fetch_live_matches: {type(e).__name__}: {e}")
    return []


def fetch_match_stats(slug: str, sport: str = "soccer") -> Dict[str, Any]:
  """Получает статистику матча с обработкой ошибок"""
  try:
    data = _post(MATCH_STATS_QUERY, {"slug": slug, "sport": sport})
    match_data = data.get("Match")
    if not match_data:
      raise ValueError(f"Match stats not found for slug {slug}")
    # Match может быть словарем или списком
    if isinstance(match_data, list):
      if not match_data:
        raise ValueError(f"Match stats not found for slug {slug}")
      return match_data[0]
    return match_data
  except Exception as e:
    # Пробрасываем ошибку дальше, чтобы анализатор мог её обработать
    raise RuntimeError(f"Failed to fetch match stats for {slug}: {e}")


def fetch_match_odds(
    slug: str,
    market: Optional[str] = None,
    limit: int = 5,
    market_limit: int = 10,
    sport: str = "soccer",
) -> List[Dict[str, Any]]:
  """Получает коэффициенты матча с обработкой ошибок"""
  try:
    data = _post(
        MATCH_ODDS_QUERY,
        {
            "slug": slug,
            "market": market,
            "limit": limit,
            "marketLimit": market_limit,
            "sport": sport,
        },
    )
    return data.get("MatchTopOdds", [])
  except Exception as e:
    # Возвращаем пустой список вместо падения - матч просто не получит коэффициенты
    print(f"WARNING: Failed to fetch odds for {slug}: {type(e).__name__}: {e}")
    return []

