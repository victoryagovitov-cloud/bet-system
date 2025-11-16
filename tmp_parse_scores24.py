import json
import re


def extract_urql_data(html: str) -> dict:
    """Extract URQL JSON payload embedded in the Scores24 live page."""
    match = re.search(r'window\.URQL_DATA=JSON\.parse\("(.+?)"\);', html, re.DOTALL)
    if not match:
        raise ValueError("URQL_DATA block not found")
    payload = match.group(1)
    print("URQL payload length:", len(payload))
    # JSON string is double-escaped, need to unescape quotes and backslashes
    decoded = bytes(payload, "utf-8").decode("unicode_escape")
    return json.loads(decoded)


def extract_store_config(html: str) -> dict:
    match = re.search(r'window\.__STORE__=(\{.*?\})\s*<', html, re.DOTALL)
    if not match:
        raise ValueError("__STORE__ block not found")
    raw = match.group(1)
    return json.loads(raw)


def inspect_live_page():
    with open("scores24_live_page.html", "r", encoding="utf-8") as f:
        html = f.read()
    data = extract_urql_data(html)
    print(f"Total entries: {len(data)}")
    for key, entry in data.items():
        print(f"\n=== Entry {key} ===")
        print(f"Keys: {list(entry.keys())}")
        payload = entry.get("data", "")
        if isinstance(payload, str):
            print(payload[:400])
            parsed_payload = json.loads(payload)
            if "leaguesList" in parsed_payload:
                leagues = parsed_payload["leaguesList"]["leagues"]
                print(f"Leagues: {len(leagues)}")
                first = leagues[0]
                print("Sample league:", first["league"]["name"])
                match = first["matches"][0]
                print("Sample match keys:", match.keys())
                print("Slug:", match["slug"])
                print("Game score:", match.get("gameScore"))
                print("Minute:", match.get("minute"), "Status:", match.get("status"))
                print("Full match data:", json.dumps(match, ensure_ascii=False)[:500])
    store = extract_store_config(html)
    print("\nStore config keys:", store.keys())
    config = store.get("config", {})
    print("Config keys:", config.keys())
    inner_config = config.get("config", {})
    print("Inner config keys:", inner_config.keys())
    for key in ("API_HOST", "WS_SUBSCRIBE_HOST", "API_GATEWAY", "GATEWAY_URL", "GRAPHQL_URL"):
        print(f"{key}:", inner_config.get(key))

def inspect_match_page():
    with open("scores24_match.html", "r", encoding="utf-8") as f:
        html = f.read()
    data = extract_urql_data(html)
    print(f"\nMatch page entries: {len(data)}")
    for key, entry in data.items():
        print(f"\n=== Match entry {key} ===")
        payload = entry.get("data", "")
        if isinstance(payload, str):
            print(payload[:400])
            if "matchStatistics" in payload:
                stats = json.loads(payload)["matchStatistics"]
                print("Sections:", [section["type"] for section in stats["sections"]])
            if "shotsOnTarget" in payload:
                parsed = json.loads(payload)
                print("Parsed keys:", list(parsed.keys()))


def main():
    inspect_live_page()
    inspect_match_page()


if __name__ == "__main__":
    main()

