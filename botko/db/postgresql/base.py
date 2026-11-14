"""PostgreSQL backend that retries opening a connection while the server restarts.

unattended-upgrades restarts Postgres when it upgrades it, which leaves it
refusing connections for a few seconds. Instead of failing every request and
task that arrives in that window, wait for the server to come back. Only
opening a connection is retried, never a query.
"""

import logging
import time

import psycopg
from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgresDatabaseWrapper,
)

logger = logging.getLogger(__name__)

# Seconds to wait before each retry (~15s in total), then one last attempt.
RETRY_DELAYS = (0.5, 1, 2, 4, 8)

# Errors that mean the server is (re)starting rather than misconfigured.
TRANSIENT_ERRORS = (
    "Connection refused",
    "the database system is shutting down",
    "the database system is starting up",
    "not yet accepting connections",
    "No such file or directory",  # the unix socket is gone while Postgres is down
)


def is_transient(error: psycopg.OperationalError) -> bool:
    message = str(error)
    return any(text in message for text in TRANSIENT_ERRORS)


class DatabaseWrapper(PostgresDatabaseWrapper):
    def get_new_connection(self, conn_params):
        for attempt, delay in enumerate(RETRY_DELAYS, start=1):
            try:
                return super().get_new_connection(conn_params)
            except psycopg.OperationalError as error:
                if not is_transient(error):
                    raise
                logger.warning(
                    "Postgres is unavailable (attempt %d/%d), retrying in %ss: %s",
                    attempt,
                    len(RETRY_DELAYS) + 1,
                    delay,
                    error,
                )
                time.sleep(delay)
        return super().get_new_connection(conn_params)
