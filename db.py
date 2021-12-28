import atexit
import os
import sqlite3

# DB INIT
connection = sqlite3.connect(
    os.environ.get("SQLITE_URL", ":memory:"), check_same_thread=False
)
connection.execute(
    "create table if not exists karma (id integer primary key, channel text not null, ts text not null, user text not null)"
)
connection.row_factory = sqlite3.Row
atexit.register(connection.close)


def connection_context(context, next):
    with connection:
        context["connection"] = connection
        next()
