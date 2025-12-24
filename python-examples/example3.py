"""
Interactive text-based exercise for the JsonServerClient.

Start the Go server first, then run:
    export API_TOKEN=secret-token
    python example3.py

Commands use slash prefixes (e.g. /list posts). Type /help to see everything.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from client import JsonServerClient, JsonServerError

DEFAULT_URL = os.getenv("JSON_SERVER_URL", "http://localhost:11220")
DEFAULT_TOKEN = os.getenv("JSON_SERVER_API_TOKEN", "secret-token")
DEFAULT_DB = os.getenv("JSON_SERVER_DB", "mybase")


def pretty_print(payload: Any) -> None:
    try:
        print(json.dumps(payload, indent=2))
    except TypeError:
        print(payload)


def parse_params(tokens: List[str]) -> Dict[str, str]:
    params: Dict[str, str] = {}
    for token in tokens:
        if "=" not in token:
            raise ValueError(f"expected key=value pair, got {token!r}")
        key, value = token.split("=", 1)
        params[key] = value
    return params


def parse_json(payload: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:  # pragma: no cover - interactive helper
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("JSON payload must be an object")
    return parsed


class InteractiveCLI:
    def __init__(self) -> None:
        self.base_url = DEFAULT_URL
        self.token = DEFAULT_TOKEN
        self.db = DEFAULT_DB

    def run(self) -> None:
        self._print_welcome()
        while True:
            try:
                raw = input("json-server> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nbye")
                break
            if not raw:
                continue
            if raw in ("/exit", "exit", "quit"):
                print("bye")
                break
            self._dispatch(raw)

    def _dispatch(self, raw: str) -> None:
        if raw in ("/help", "help"):
            self._print_help()
            return
        parts = raw.split()
        command = parts[0]
        try:
            if command == "/url":
                self._set_url(parts)
            elif command == "/token":
                self._set_token(parts)
            elif command == "/db":
                self._set_db(parts)
            elif command == "/state":
                self._print_state()
            elif command == "/showdb":
                self._show_db(parts)
            elif command == "/list":
                self._list(parts)
            elif command == "/get":
                self._get(parts)
            elif command == "/create":
                self._create(raw)
            elif command == "/replace":
                self._replace(raw)
            elif command == "/patch":
                self._patch(raw)
            elif command == "/delete":
                self._delete(parts)
            else:
                print(f"Unknown command: {command}. Try /help.")
        except (ValueError, IndexError) as exc:
            print(f"Usage error: {exc}")
        except JsonServerError as exc:
            print(f"API error {exc.status}: {exc.message}")
            if exc.payload:
                pretty_print(exc.payload)

    def _client(self) -> JsonServerClient:
        return JsonServerClient(base_url=self.base_url, token=self.token)

    def _set_url(self, parts: List[str]) -> None:
        self.base_url = parts[1]
        print(f"Base URL set to {self.base_url}")

    def _set_token(self, parts: List[str]) -> None:
        self.token = parts[1]
        print("Token updated")

    def _set_db(self, parts: List[str]) -> None:
        self.db = parts[1]
        print(f"Default db set to {self.db}")

    def _print_state(self) -> None:
        print(f"URL: {self.base_url}")
        print(f"DB:  {self.db}")
        print(f"TOK: {self.token}")

    def _show_db(self, parts: List[str]) -> None:
        db_name = parts[1] if len(parts) > 1 else self.db
        client = self._client()
        pretty_print(client.db(db_name))

    def _list(self, parts: List[str]) -> None:
        if len(parts) < 2:
            raise ValueError("/list <collection> [key=value ...]")
        collection = parts[1]
        params = parse_params(parts[2:]) if len(parts) > 2 else None
        client = self._client()
        pretty_print(client.list(self.db, collection, params=params))

    def _get(self, parts: List[str]) -> None:
        if len(parts) < 3:
            raise ValueError("/get <collection> <id>")
        collection, item_id = parts[1], parts[2]
        client = self._client()
        pretty_print(client.get(self.db, collection, item_id) )

    def _create(self, raw: str) -> None:
        # /create <collection> <json>
        parts = raw.split(maxsplit=2)
        if len(parts) < 3:
            raise ValueError("/create <collection> <json-payload>")
        collection, payload_str = parts[1], parts[2]
        payload = parse_json(payload_str)
        client = self._client()
        pretty_print(client.create(self.db, collection, payload) )

    def _replace(self, raw: str) -> None:
        # /replace <collection> <id> <json>
        parts = raw.split(maxsplit=3)
        if len(parts) < 4:
            raise ValueError("/replace <collection> <id> <json-payload>")
        collection, item_id, payload_str = parts[1], parts[2], parts[3]
        payload = parse_json(payload_str)
        client = self._client()
        pretty_print(client.replace(self.db, collection, item_id, payload) )

    def _patch(self, raw: str) -> None:
        # /patch <collection> <id> <json>
        parts = raw.split(maxsplit=3)
        if len(parts) < 4:
            raise ValueError("/patch <collection> <id> <json-payload>")
        collection, item_id, payload_str = parts[1], parts[2], parts[3]
        payload = parse_json(payload_str)
        client = self._client()
        pretty_print(client.patch(self.db, collection, item_id, payload))

    def _delete(self, parts: List[str]) -> None:
        if len(parts) < 3:
            raise ValueError("/delete <collection> <id>")
        collection, item_id = parts[1], parts[2]
        client = self._client()
        client.delete(self.db, collection, item_id)
        print("deleted")

    def _print_welcome(self) -> None:
        print("JsonServerClient interactive demo. Type /help to see commands.")
        self._print_state()

    def _print_help(self) -> None:
        print(
            """
Commands:
  /url <url>                  Set base URL (current is shown in /state)
  /token <token>              Set bearer token
  /db <name>                  Set default database name
  /state                      Show current settings
  /showdb [db]                Fetch entire database (default uses /db setting)
  /list <collection> [q...]   List a collection; optional key=value filters
  /get <collection> <id>      Get one item by id
  /create <collection> <json> Create an item with JSON object
  /replace <collection> <id> <json>  PUT an entire object
  /patch <collection> <id> <json>    PATCH partial fields
  /delete <collection> <id>   Delete an item
  /exit                       Quit
Examples:
  /list posts author=codex _limit=1
  /create posts {"title": "Hi", "author": "me"}
  /patch posts 1 {"title": "Updated"}
"""
        )


if __name__ == "__main__":
    InteractiveCLI().run()
