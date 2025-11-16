import json
import sys
from typing import Any, Dict, List, Optional

import requests


GRAPHQL_URL = "https://scores24.live/graphql"


def load_query_fields() -> List[Dict[str, Any]]:
    query = """
    query {
      __schema {
        queryType {
          fields {
            name
            args {
              name
              type {
                name
                kind
                ofType {
                  name
                  kind
                  ofType {
                    name
                    kind
                  }
                }
              }
            }
            type {
              name
              kind
              ofType {
                name
                kind
                ofType {
                  name
                  kind
                }
              }
            }
          }
        }
      }
    }
    """
    response = requests.post(
        GRAPHQL_URL,
        json={"query": query},
        verify=False,
    )
    response.raise_for_status()
    data = response.json()
    return data["data"]["__schema"]["queryType"]["fields"]


def load_type(type_name: str) -> Optional[Dict[str, Any]]:
    query = """
    query ($type: String!) {
      __type(name: $type) {
        name
        kind
        fields {
          name
          type {
            name
            kind
            ofType {
              name
              kind
              ofType {
                name
                kind
              }
            }
          }
        }
        enumValues {
          name
        }
      }
    }
    """
    response = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": {"type": type_name}},
        verify=False,
    )
    response.raise_for_status()
    return response.json()["data"]["__type"]


def introspect(field_name: str) -> Dict[str, Any]:
    fields = load_query_fields()
    for field in fields:
        if field["name"] == field_name:
            return field
    raise ValueError(f"Field {field_name} not found")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python introspect_field.py <FieldName>")
        sys.exit(1)
    field = sys.argv[1]
    if field.startswith("type:"):
        type_name = field.split(":", 1)[1]
        type_info = load_type(type_name)
        print(json.dumps(type_info, ensure_ascii=False, indent=2))
        return
    field_data = introspect(field)
    print(json.dumps(field_data, ensure_ascii=False, indent=2))
    if field_data.get("type", {}).get("name"):
        type_info = load_type(field_data["type"]["name"])
        if type_info:
            print("\n=== Type definition ===")
            print(json.dumps(type_info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

