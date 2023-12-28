import re
import sqlite3
from datetime import datetime, timedelta


def insert_karma(
    connection: sqlite3.Cursor, channel: str, ts: str, users: list[str]
) -> None:
    values = [(channel, ts, user) for user in users]
    connection.executemany(
        "INSERT INTO karma (channel, ts, user) values (?, ?, ?)", values
    )


def fetch_karma_leaderboard(connection: sqlite3.Cursor) -> sqlite3.Cursor:
    return connection.execute(
        "SELECT COUNT(*) as count, user FROM karma WHERE strftime('%Y', datetime(ts, 'unixepoch')) = ? GROUP BY user ORDER BY count DESC",
        (str(datetime.now().year),),
    )


def fetch_karma_leaderboard_prev_month(
    connection: sqlite3.Cursor,
) -> sqlite3.Cursor:
    prev_month = datetime.now().replace(day=1) - timedelta(days=1)
    return connection.execute(
        "SELECT COUNT(*) as count, user FROM karma WHERE strftime('%Y-%m', datetime(ts, 'unixepoch')) = ? GROUP BY user ORDER BY count DESC",
        (prev_month.strftime("%Y-%m"),),
    )


def fetch_karma_leaderboard_prev_year(
    connection: sqlite3.Cursor,
) -> sqlite3.Cursor:
    prev_year = datetime.now().replace(day=1, month=1) - timedelta(days=1)
    return connection.execute(
        "SELECT COUNT(*) as count, user FROM karma WHERE strftime('%Y', datetime(ts, 'unixepoch')) = ? GROUP BY user ORDER BY count DESC",
        (prev_year.strftime("%Y"),),
    )


def insert_birthday(
    connection: sqlite3.Cursor, user: str, day: int, month: int
) -> None:
    connection.execute(
        "INSERT INTO birthday (user, day, month) values (?, ?, ?)",
        (user, day, month),
    )


def fetch_birthdays(connection: sqlite3.Cursor, day: int, month: int) -> sqlite3.Cursor:
    return connection.execute(
        "SELECT user FROM birthday WHERE day = ? AND month = ?",
        (day, month),
    )


def parse_karma_from_text(text: str) -> list[str]:
    users = [match for match in re.findall(r"<@(U[A-Z0-9]*)>.?\+\+", text)]
    return users
