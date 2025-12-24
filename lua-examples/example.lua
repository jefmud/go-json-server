-- Minimal Lua client example for the Go JSON server.
-- Requires: LuaSocket (socket.http, ltn12) and dkjson (or any json lib with encode/decode).
--
-- Usage:
--   API_TOKEN=secret-token JSON_SERVER_URL=http://localhost:43210 lua example.lua

local http = require("socket.http")
local ltn12 = require("ltn12")
local json = require("dkjson")

local BASE_URL = os.getenv("JSON_SERVER_URL") or "http://localhost:43210"
local TOKEN = os.getenv("JSON_SERVER_API_TOKEN") or ""
local DB = os.getenv("JSON_SERVER_DB") or "db"

if TOKEN == "" then
  error("JSON_SERVER_API_TOKEN is required")
end

local function request(method, path, bodyTable)
  local headers = { ["Authorization"] = "Bearer " .. TOKEN }
  local body
  if bodyTable then
    body = json.encode(bodyTable)
    headers["Content-Type"] = "application/json"
    headers["Content-Length"] = tostring(#body)
  end

  local respChunks = {}
  local _, code, respHeaders, statusLine = http.request{
    url = BASE_URL .. path,
    method = method,
    headers = headers,
    source = body and ltn12.source.string(body) or nil,
    sink = ltn12.sink.table(respChunks),
  }

  local raw = table.concat(respChunks)
  local decoded = raw
  if respHeaders and respHeaders["content-type"] and respHeaders["content-type"]:find("application/json") then
    decoded = json.decode(raw)
  end

  local status = tonumber(code) or 0
  if status >= 400 then
    error(string.format("HTTP %d: %s (%s)", status, raw, statusLine or ""))
  end

  return decoded
end

local function demo()
  print("# Listing posts")
  local posts = request("GET", "/api/" .. DB .. "/posts")
  print(json.encode(posts, { indent = true }))

  print("\n# Creating a post")
  local created = request("POST", "/api/" .. DB .. "/posts", { title = "Hello from Lua", author = "example" })
  print(json.encode(created, { indent = true }))

  print("\n# Fetching by id")
  local fetched = request("GET", "/api/" .. DB .. "/posts/" .. created.id)
  print(json.encode(fetched, { indent = true }))

  print("\n# Patching title")
  local patched = request("PATCH", "/api/" .. DB .. "/posts/" .. created.id, { title = "Updated by Lua" })
  print(json.encode(patched, { indent = true }))

  print("\n# Deleting")
  request("DELETE", "/api/" .. DB .. "/posts/" .. created.id)
  print("deleted")
end

demo()
