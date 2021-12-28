import atexit
import logging
import os
import sqlite3

logger = logging.getLogger("uvicorn.db")

# DB INIT
DATABASE_URL = os.environ.get("DATABASE_URL", ":memory:")

logger.info("📀 Loading data from %s", DATABASE_URL)
connection = sqlite3.connect(
    DATABASE_URL,
    check_same_thread=False,  # TODO: We might have to open it on every connection
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
