import json
import sys
from typing import Any, Dict

import requests


GRAPHQL_URL = "https://scores24.live/graphql"

QUERY = """
query ($slug: String!) {
  Match(slug: $slug, sport_slug: "soccer") {
    slug
    minute
    game_score
    status {
      code
    }
    teams {
      name
      position
    }
    statistic {
      t1 {
        ball_possession
        shots_on_goal
        shots_total
      }
      t2 {
        ball_possession
        shots_on_goal
        shots_total
      }
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
  }
}
"""


def fetch_match_stats(slug: str) -> Dict[str, Any]:
    response = requests.post(
        GRAPHQL_URL,
        json={"query": QUERY, "variables": {"slug": slug}},
        verify=False,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python graphql_match_stats.py <match-slug>")
        sys.exit(1)
    slug = sys.argv[1]
    data = fetch_match_stats(slug)
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

