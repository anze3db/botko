import re
import sqlite3
from datetime import datetime


def insert_karma(connection: sqlite3.Connection, values: list[tuple[str, str, str]]):
    connection.executemany(
        "INSERT INTO karma (channel, ts, user) values (?, ?, ?)", values
    )


def parse_karma_from_text(message: dict[str, str], connection: sqlite3.Connection):
    text = message.get("text", "")
    names = [
        (message["channel"], message["ts"], match)
        for match in re.findall(r"<@(U[A-Z0-9]*)>.?\+\+", text)
    ]
    insert_karma(connection, names)
    return names


def karma_leaderboard(connection: sqlite3.Connection):
    return connection.execute(
        "SELECT COUNT(*) as count, user FROM karma WHERE strftime('%Y', datetime(ts, 'unixepoch')) = ? GROUP BY user ORDER BY count DESC",
        (str(datetime.now().year),),
    )
