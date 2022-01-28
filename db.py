import atexit
import logging
import os
import sqlite3
from functools import cache

logger = logging.getLogger("uvicorn.db")


@cache
def get_connection(url: str = None) -> sqlite3.Connection:
    # DB INIT
    if not url:
        url = ":memory:"

    logger.info("📀 Loading data from %s", url)
    connection = sqlite3.connect(
        url,
        check_same_thread=False,  # TODO: We might have to open it on every connection
    )
    connection.execute(
        "create table if not exists karma (id integer primary key, channel text not null, ts text not null, user text not null)"
    )
    connection.row_factory = sqlite3.Row
    atexit.register(connection.close)
    return connection


def connection_context(context, next):
    context["connection"] = get_connection(os.environ.get("DATABASE_URL", ":memory:"))
    next()
