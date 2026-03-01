"""
One-time migration script: SQLite → PostgreSQL via Django ORM.

Usage:
    uv run python migrate_data.py path/to/botko.db

Delete this file after migration is complete.
"""

import os
import sqlite3
import sys
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "botko.settings")

import django

django.setup()

from bot.models import Birthday, Karma


def migrate(sqlite_path: str):
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row

    # Migrate karma
    rows = conn.execute("SELECT channel, ts, user FROM karma").fetchall()
    karma_objects = []
    for row in rows:
        try:
            created_at = datetime.fromtimestamp(float(row["ts"]))
        except (ValueError, OSError):
            created_at = datetime.now()
        karma_objects.append(
            Karma(
                channel=row["channel"],
                ts=row["ts"],
                user=row["user"],
                created_at=created_at,
            )
        )
    Karma.objects.bulk_create(karma_objects, batch_size=1000)
    print(f"Migrated {len(karma_objects)} karma rows.")

    # Migrate birthdays (deduplicate)
    rows = conn.execute("SELECT user, day, month FROM birthday").fetchall()
    seen = set()
    birthday_objects = []
    for row in rows:
        if row["user"] not in seen:
            seen.add(row["user"])
            birthday_objects.append(
                Birthday(user=row["user"], day=row["day"], month=row["month"])
            )
    Birthday.objects.bulk_create(birthday_objects, batch_size=1000)
    print(
        f"Migrated {len(birthday_objects)} birthday rows (deduplicated from {len(rows)})."
    )

    conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-sqlite-db>")
        sys.exit(1)
    migrate(sys.argv[1])
