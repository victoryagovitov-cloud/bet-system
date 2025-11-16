from scores24_graphql_client import fetch_live_matches, fetch_match_stats


def main() -> None:
    matches = fetch_live_matches(5)
    print(f"Got {len(matches)} live matches")
    for idx, match in enumerate(matches, 1):
        slug = match["slug"]
        print(f"\n[{idx}] {slug} minute={match.get('minute')} state={match.get('game_state')}")
        details = fetch_match_stats(slug)
        print("  detail keys:", list(details.keys()))
        print(
            "  scoreboard:",
            details.get("game_state"),
            "game_score:",
            details.get("game_score"),
            "result_score:",
            details.get("result_score"),
            "result_scores:",
            details.get("result_scores"),
        )
        print("  teams:", [t.get("name") for t in details.get("teams", [])])
        stat = details.get("statistic", {})
        periods = stat.get("periods") or []
        total = next((p for p in periods if p.get("type") == "total"), None)
        if total:
            key_group = next((g for g in total.get("groups", []) if g.get("type") == "key_stat"), None)
            if key_group:
                print("  key stats:", key_group.get("items"))
        else:
            print("  no total stats yet")
        standings = details.get("standings") or []
        if standings:
            print("  standings sample:", standings[:2])


if __name__ == "__main__":
    main()

