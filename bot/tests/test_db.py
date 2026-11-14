from unittest.mock import Mock, patch

import psycopg
import pytest
from django.conf import settings
from django.db import connection, connections

from botko.db.postgresql.base import DatabaseWrapper

PARENT = "django.db.backends.postgresql.base.DatabaseWrapper.get_new_connection"


def test_settings():
    assert settings.DATABASES["default"]["CONN_HEALTH_CHECKS"] is True
    assert settings.DATABASES["default"]["ENGINE"] == "botko.db.postgresql"
    assert isinstance(connections["default"], DatabaseWrapper)


@patch("botko.db.postgresql.base.time.sleep", autospec=True)
def test_retries_while_postgres_restarts(sleep):
    conn = Mock()
    refused = psycopg.OperationalError(
        'connection failed: connection to server at "127.0.0.1", port 5432 failed: '
        "Connection refused"
    )
    with patch(PARENT, autospec=True, side_effect=[refused, refused, conn]) as parent:
        assert connection.get_new_connection({}) is conn
    assert parent.call_count == 3
    assert [c.args for c in sleep.call_args_list] == [(0.5,), (1,)]


@patch("botko.db.postgresql.base.time.sleep", autospec=True)
def test_gives_up_after_last_attempt(sleep):
    error = psycopg.OperationalError("the database system is shutting down")
    with (
        patch(PARENT, autospec=True, side_effect=error) as parent,
        pytest.raises(psycopg.OperationalError),
    ):
        connection.get_new_connection({})
    assert parent.call_count == 6
    assert sleep.call_count == 5


@patch("botko.db.postgresql.base.time.sleep", autospec=True)
def test_does_not_retry_other_errors(sleep):
    error = psycopg.OperationalError('password authentication failed for user "botko"')
    with (
        patch(PARENT, autospec=True, side_effect=error) as parent,
        pytest.raises(psycopg.OperationalError, match="password authentication"),
    ):
        connection.get_new_connection({})
    assert parent.call_count == 1
    sleep.assert_not_called()
