import os

from client import JsonServerClient, JsonServerError

TOKEN = os.getenv("JSON_SERVER_API_TOKEN", "")
URL = os.getenv("JSON_SERVER_URL", "http://localhost:43210")

# show menu
def menu():
    print("=== JsonServerClient CLI ===")
    print("/url <url>")
    print("/token <token>")
    print("/list <db> <collection>")
    print("/get <db> <collection> <id>")
    print("/delete <db> <collection> <id>")
    print("/exit")
    res = input("> ")
    return res

def parse_command(command):
    parts = command.split(" ")
    return parts[0], parts[1:]

def set_token(token):
    global TOKEN
    print(f"Token set to {token}")
    TOKEN = token
def newdb():
    print("Creating new database")
    client = JsonServerClient(base_url=URL, token=TOKEN)
    client.db("newdb")


def get_url(url):
    global URL
    print(f"URL set to {url}")
    URL = url

def list_database(db):
    print(f"Listing database {db}")
    client = JsonServerClient(base_url=URL, token=TOKEN)
    posts = client.list(db, "posts")
    print(posts)


def list_collection(db, collection):
    print(f"Listing {collection} in {db}")
    client = JsonServerClient(base_url=URL, token=TOKEN)
    try:
        items = client.list(db, collection)
    except JsonServerError as exc:
        print(f"API error {exc.status}: {exc.message}")
        return
    print(items)


def get_item(db, collection, item_id):
    print(f"Getting {collection}/{item_id} from {db}")
    client = JsonServerClient(base_url=URL, token=TOKEN)
    try:
        item = client.get(db, collection, item_id)
    except JsonServerError as exc:
        print(f"API error {exc.status}: {exc.message}")
        return
    print(item)


def delete_item(db, collection, item_id):
    print(f"Deleting {collection}/{item_id} from {db}")
    client = JsonServerClient(base_url=URL, token=TOKEN)
    try:
        client.delete(db, collection, item_id)
    except JsonServerError as exc:
        print(f"API error {exc.status}: {exc.message}")
        return
    print("deleted")

if __name__ == "__main__":
    if not TOKEN:
        print("Set API_TOKEN or use /token to provide a bearer token.")
    while True:
        command = menu()
        action, args = parse_command(command)
        if action == "/url":
            get_url(args[0])
        elif action == "/token":
            set_token(args[0])
        elif action == "/list":
            list_collection(args[0], args[1])
        elif action == "/get":
            get_item(args[0], args[1], args[2])
        elif action == "/delete":
            delete_item(args[0], args[1], args[2])
        elif action == "/exit":
            break
