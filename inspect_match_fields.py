from scores24_graphql_client import fetch_live_matches, fetch_match_stats


def main():
    matches = fetch_live_matches(5)
    for match in matches:
        details = fetch_match_stats(match["slug"])
        print("Slug:", match["slug"])
        print("Minute list:", match.get("minute"))
        print("Minute details:", details.get("minute"))
        print("Teams:", [t.get("name") for t in details.get("teams", [])])
        print("Status list:", (match.get("status") or {}).get("code"))
        print("Status details:", (details.get("status") or {}).get("code"))
        print("-" * 40)
        break


if __name__ == "__main__":
    main()

