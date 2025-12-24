"""
Example usage of the JsonServerClient.

Run:
    export JSON_SERVER_API_TOKEN=secret-token
    python example.py --base-url http://localhost:43210 --db db
"""

import argparse
import os
import sys
from typing import Any, Dict

from client import JsonServerClient, JsonServerError


def main() -> int:
    parser = argparse.ArgumentParser(description="Demo for the Go JSON server client.")
    parser.add_argument("--base-url", default="http://localhost:43210", help="Server base URL")
    parser.add_argument("--db", default="db", help="Database name (json filename without .json)")
    parser.add_argument("--token", default=os.getenv("JSON_SERVER_API_TOKEN", ""), help="API token (or set JSON_SERVER_API_TOKEN)")
    args = parser.parse_args()

    if not args.token:
        parser.error("Token is required (use --token or set API_TOKEN)")

    client = JsonServerClient(base_url=args.base_url, token=args.token)

    try:
        print(f"# Listing posts in {args.db}")
        posts = client.list(args.db, "posts")
        print(posts)
    except JsonServerError as exc:
        print(f"API error {exc.status}: {exc.message}", file=sys.stderr)

    try:
        print("\n# Creating a post")
        new_post: Dict[str, Any] = {"title": "Hello from Python client", "author": "example"}
        created = client.create(args.db, "posts", new_post)
        print(created)

        print("\n# Fetching the post by id")
        fetched = client.get(args.db, "posts", created["id"])
        print(fetched)

        print("\n# Patching the post title")
        patched = client.patch(args.db, "posts", created["id"], {"title": "Updated title"})
        print(patched)

        print("\n# Deleting the post")
        client.delete(args.db, "posts", created["id"])
        print("deleted")

    except JsonServerError as exc:
        print(f"API error {exc.status}: {exc.message}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - simple demo error path
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
