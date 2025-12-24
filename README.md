Go JSON Server
==============

A minimal Go language JSON database inspired by `typicode/json-server` (https://github.com/typicode/json-server) that serves RESTful CRUD endpoints
backed by JSON files on disk. Each API is mounted at `/api/<json>`,
where `<json>` is the base name of a JSON file located in `./json`.

Disclaimer: This server is intended to be used in lightweight projects and definitely not for production
where security and speed are important!

Features
--------
- Token-based authentication via the `Authorization: Bearer <token>` header.
- Serves any JSON file in `./json` at `/api/<name>` (e.g., `json/db.json` -> `/api/db`).
- CRUD for collections: `GET`/`POST /api/<db>/<collection>`, `GET`/`PUT`/`PATCH`/`DELETE /api/<db>/<collection>/<id>`.
- Creates missing JSON databases on the first write (POST/PUT/PATCH/DELETE).
- Optional request logging to stdout (`-verbose`) or a file (`-log-file`), including client IP, method, path, status, and duration.
- Simple filtering, sorting, and pagination with `_sort`, `_order`, `_limit`, `_page` query params.
- Writes changes back to the source JSON file.
- Very lightweight (on resources)

Getting Started
---------------
1) Set an API token (required):
```
export JSON_SERVER_API_TOKEN=secret-token
```

2) Add or edit JSON files in `json/`. A starter `json/db.json` is included.

3) Run the server:

This will vary with the type of installation.  You may run it via source code with 'Go' language or
via an executable for your platform.  All the same command line switches function for either.

### Via Executable

```aiignore
./json-server                   # listens on 0.0.0.0:43210
./json-server -host 127.0.0.1   # more secure, localhost only
```

### Via Go Language (locally installed)

```
go run .                # listens on 0.0.0.0:43210
go run . -host 127.0.0.1  # bind only to localhost
```
Flags:
- `-host` (default `0.0.0.0` for all interfaces)
- `-port` (default `43210`)
- `-token` (overrides `JSON_SERVER_API_TOKEN`)
- `-json-dir` (default `json`)
- `-verbose` (log requests to stdout)
- `-log-file` (path to append request logs; works with or without `-verbose`)

Example Requests
----------------
Assuming `JSON_SERVER_API_TOKEN=secret-token`:
- List collections: `GET /api/db` -> full contents of `json/db.json`
- List posts: `GET /api/db/posts`
- Filter (supports dot-paths + wildcards): `GET /api/db/posts?author.name=codex` or `GET /api/db/posts?title=Hello*`
- Sort/limit: `GET /api/db/posts?_sort=id&_order=desc&_limit=1`
- Read one: `GET /api/db/posts/1`
- Create: `POST /api/db/posts` with body `{"title":"New","author":"me"}`
- Replace: `PUT /api/db/posts/1` with full object
- Patch: `PATCH /api/db/posts/1` with partial fields
- Delete: `DELETE /api/db/posts/1`

Headers
-------
All requests must include `Authorization: Bearer <token>`.

Python Client
-------------
The project provides a simple `client.py` which provides a thin helper using `requests` module:

```python
from client import JsonServerClient

client = JsonServerClient(base_url="http://localhost:43210", token="secret-token")
posts = client.list("db", "posts")
created = client.create("db", "posts", {"title": "New", "author": "me"})
one = client.get("db", "posts", created["id"])
client.patch("db", "posts", created["id"], {"title": "Updated"})
client.delete("db", "posts", created["id"])
```

Tests
-----
Run the Go test suite (set a local cache path to avoid permission issues):
```
GOCACHE="$(pwd)/.gocache" go test ./...
```

Language Examples
-----------------
- Python: see `python-examples/` for CLI demos using `client.py`.
- Lua: `lua-examples/example.lua` (requires LuaSocket + dkjson).
- JavaScript/Node: `javascript-examples/example.js` (Node 18+).

Notes
-----
- The `<json>` segment must match a filename in `./json` (without the `.json` suffix).
- To create a new database while the server is running, just write to it: e.g. `POST /api/newdb/posts` will create `json/newdb.json` and start the `posts` collection.
- IDs auto-increment when the collection already uses numeric IDs; otherwise a UUIDv4 is generated. You can also supply your own `"id"` value in the payload (uniqueness is not enforced when you do).
- Collections must be arrays in the JSON file. IMPORTANT: Non-array collections return `400 Bad Request`.
