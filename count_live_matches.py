from scores24_graphql_client import fetch_live_matches


def main():
    matches = fetch_live_matches(100)
    print("Total live matches fetched:", len(matches))


if __name__ == "__main__":
    main()

