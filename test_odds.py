from scores24_graphql_client import fetch_live_matches, fetch_match_odds


def main() -> None:
    live = fetch_live_matches(20)
    all_names = set()
    for m in live:
        odds = fetch_match_odds(m["slug"], market=None)
        names = {
            value["bookmaker"]["name"]
            for market in odds
            for rate in market.get("topRates", [])
            for value in rate.get("values", [])
            if value.get("bookmaker")
        }
        all_names.update(names)
    print("total bookmakers:", all_names)


if __name__ == "__main__":
    main()

