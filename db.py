import logging
import os
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger("uvicorn.db")


@contextmanager
def get_connection(url=None):
    if url is None:
        url = os.environ.get("DATABASE_URL", ":memory:")
    logger.info("📀 Connecting to %s", url)
    connection = sqlite3.connect(url)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    yield cursor
    connection.commit()
    connection.close()
    logger.info("📀 Closed connection to %s", url)


def init_db(cursor):
    cursor.execute(
        "create table if not exists karma (id integer primary key, channel text not null, ts text not null, user text not null)"
    )
    cursor.execute(
        "create table if not exists birthday (id integer primary key, user text not null, day integer not null, month integer not null)"
    )
