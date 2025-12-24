// Minimal Node client example for the Go JSON server.
// Requires Node >= 18 (built-in fetch). Usage:
//   API_TOKEN=secret-token node example.js

const BASE_URL = process.env.JSON_SERVER_URL || "http://localhost:43210";
const TOKEN = process.env.JSON_SERVER_API_TOKEN || "";
const DB = process.env.JSON_SERVER_DB || "db";

if (!TOKEN) {
  console.error("API_TOKEN is required");
  process.exit(1);
}

async function request(method, path, body) {
  const headers = {
    Authorization: `Bearer ${TOKEN}`,
  };
  const init = { method, headers };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }

  const res = await fetch(`${BASE_URL}${path}`, init);
  const text = await res.text();
  let payload;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch {
    payload = text;
  }
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${JSON.stringify(payload)}`);
  }
  return payload;
}

async function demo() {
  console.log("# Listing posts");
  const posts = await request("GET", `/api/${DB}/posts`);
  console.log(posts);

  console.log("\n# Creating a post");
  const created = await request("POST", `/api/${DB}/posts`, {
    title: "Hello from Node",
    author: "example",
  });
  console.log(created);

  console.log("\n# Fetching by id");
  const fetched = await request("GET", `/api/${DB}/posts/${created.id}`);
  console.log(fetched);

  console.log("\n# Patching title");
  const patched = await request("PATCH", `/api/${DB}/posts/${created.id}`, {
    title: "Updated by Node",
  });
  console.log(patched);

  console.log("\n# Deleting");
  await request("DELETE", `/api/${DB}/posts/${created.id}`);
  console.log("deleted");
}

demo().catch((err) => {
  console.error(err);
  process.exit(1);
});
