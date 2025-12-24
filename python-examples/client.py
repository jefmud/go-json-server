"""
Thin Python client for the Go JSON server.

Example:
    from client import JsonServerClient

    client = JsonServerClient(base_url="http://localhost:8080", token="secret-token")
    posts = client.list("posts", db="db")
    created = client.create("posts", {"title": "Hello", "author": "me"})
    one = client.get("posts", created["id"])
    client.patch("posts", created["id"], {"title": "Updated"})
    client.delete("posts", created["id"])
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import requests


class JsonServerError(Exception):
    """HTTP error raised by JsonServerClient."""

    def __init__(self, status: int, message: str, payload: Any = None):
        self.status = status
        self.message = message
        self.payload = payload
        super().__init__(f"{status}: {message}")


class JsonServerClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        token: str = "",
        timeout: float = 5.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        if not token:
            raise ValueError("token is required")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def list(self, db: str, collection: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        """GET /api/<db>/<collection> with optional query params."""
        return self._request("GET", self._url(db, collection), params=params)

    def get(self, db: str, collection: str, item_id: Any, payload: Dict[str, Any] = None) -> Any:
        """GET /api/<db>/<collection>/<id>."""
        return self._request("GET", self._url(db, collection, str(item_id)))

    def create(self, db: str, collection: str, payload: Dict[str, Any]) -> Any:
        """POST /api/<db>/<collection> with JSON body."""
        return self._request("POST", self._url(db, collection), json=payload)

    def replace(self, db: str, collection: str, item_id: Any, payload: Dict[str, Any]) -> Any:
        """PUT /api/<db>/<collection>/<id> with full JSON body."""
        return self._request("PUT", self._url(db, collection, str(item_id)), json=payload)

    def patch(self, db: str, collection: str, item_id: Any, payload: Dict[str, Any]) -> Any:
        """PATCH /api/<db>/<collection>/<id> with partial JSON body."""
        return self._request("PATCH", self._url(db, collection, str(item_id)), json=payload)

    def delete(self, db: str, collection: str, item_id: Any) -> None:
        """DELETE /api/<db>/<collection>/<id>."""
        self._request("DELETE", self._url(db, collection, str(item_id)))

    def db(self, db: str) -> Dict[str, Any]:
        """GET /api/<db> for the entire JSON file."""
        return self._request("GET", self._url(db))

    def db_ids(self, db: str, collection: str) -> Dict[str, Any]:
        """GET /api/<db>/<collection> get collection ids."""
        try:
            ids = [item["id"] for item in self.list(db, collection)]
            return ids
        except JsonServerError as exc:
            if exc.status == 404:
                return []



    def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        resp = self.session.request(method, url, params=params, json=json, timeout=self.timeout)
        if not resp.ok:
            self._raise_error(resp)
        if resp.status_code == 204:
            return None
        if resp.headers.get("Content-Type", "").startswith("application/json"):
            return resp.json()
        return resp.text

    def _raise_error(self, resp: requests.Response) -> None:
        try:
            payload = resp.json()
            message = payload.get("error") or payload
        except ValueError:
            payload = resp.text
            message = payload or resp.reason
        raise JsonServerError(resp.status_code, str(message), payload=payload)

    def _url(self, db: str, *segments: Iterable[str]) -> str:
        path_parts = [self.base_url, "api", db]
        for seg in segments:
            path_parts.append(str(seg).strip("/"))
        return "/".join(part.strip("/") for part in path_parts)
