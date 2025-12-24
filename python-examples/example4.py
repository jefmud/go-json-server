# work
import uuid
from client import JsonServerClient, JsonServerError
from faker import Faker
import random
import datetime

# use faker package to generate example data
fake = Faker()

client = JsonServerClient(base_url="http://localhost:43210", token="secret-token")
db_name = "example4"
collection = "users"

while True:
    try:
        res = client.db(db_name)
        ids = client.db_ids(db_name, collection)
        print(ids)
        print(f"There are {len(ids)} users in the database")
    except JsonServerError as exc:
        ids = []
        print(f"API error {exc.status}: {exc.message}")

    if len(ids) > 0:
        res = input("How many random objects to read? (0 to exit): ")
        if res != "":
            start = datetime.datetime.now()
            for i in range(int(res)):
                obj_id = random.choice(ids)
                print(client.get(db_name, collection, obj_id))
            end = datetime.datetime.now()
            elapsed = end - start
            print(f"Elapsed time: {elapsed}")

    try:
        res = input("How many objects to create? (0 to exit): ")
        count = int(res)
    except ValueError:
        exit(0)

    if count > 0:
        n = count
        print(f"Creating {n} objects")
        start = datetime.datetime.now()
        for i in range(n):
            data = {
                "name": fake.name(),
                "age": random.randint(20, 60),
                "email": fake.email(),
                "phone": fake.phone_number(),
                "city": fake.city(),
                "company": fake.company(),
                "job": fake.job()
            }
            client.create(db_name, collection, data)
        end = datetime.datetime.now()
        elapsed = end - start
        print(f"Write {n} Elapsed time: {elapsed}")

    try:
        res = input("How many object to Delete? (0 to exit): ")
        limit = int(res)
    except ValueError:
        exit(0)

    count = 0
    if res != "":
        ids = client.db_ids(db_name, collection)
        if limit > len(ids):
            limit = len(ids)
        start = datetime.datetime.now()
        for obj_id in ids:
            if count < limit:
                client.delete(db_name, collection, obj_id)
                count += 1
        print(f"Deleted {count} objects")
        end = datetime.datetime.now()
        elapsed = end - start
        print(f"Delete {int(res)} Elapsed time: {elapsed}")