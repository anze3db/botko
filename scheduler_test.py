import datetime
import sqlite3
import time
from unittest.mock import Mock

import freezegun
import pytest
from slack_sdk.web.client import WebClient

import scheduler
from db import get_connection
from models import insert_karma


@pytest.fixture(name="connection")
def fixture_connection():
    connection = get_connection(":memory:")
    connection.execute("BEGIN")
    yield connection
    connection.execute("ROLLBACK")


def test_schedule():
    assert [
        (job.at_time, job.interval, job.period) for job in scheduler.schedule.get_jobs()
    ] == [(datetime.time(10, 0), 1, datetime.timedelta(days=1))]


def test_job_no_karma(connection: sqlite3.Connection):
    scheduler.job(connection, client_mock := Mock(spec=WebClient()))
    client_mock.chat_postMessage.assert_called()
    assert (
        client_mock.chat_postMessage.call_args[1]["blocks"][1]["text"]["text"]
        == "Nobody received any Karma last month :cry:"
    )


@freezegun.freeze_time("2022-01-01 10:00:00")
def test_job_karma(connection: sqlite3.Connection):
    insert_karma(
        connection,
        channel="C02SBSSCMR7",
        ts=f"{time.time() - 12 * 60 * 60}",
        users=["U123123", "U123124"],
    )
    # Previous month shouldn't be counted
    insert_karma(
        connection,
        channel="C02SBSSCMR7",
        ts=f"{time.time() - 32 * 24 * 60 * 60}",
        users=["U123123", "U123124"],
    )
    # Current month shouldn't be counted
    insert_karma(
        connection,
        channel="C02SBSSCMR7",
        ts=f"{time.time()}",
        users=["U123123", "U123124"],
    )

    scheduler.job(connection, client_mock := Mock(spec=WebClient()))
    client_mock.chat_postMessage.assert_called()
    assert (
        client_mock.chat_postMessage.call_args[1]["blocks"][1]["text"]["text"]
        == "<@U123124> gained 1 karma."
    )
    assert (
        client_mock.chat_postMessage.call_args[1]["blocks"][2]["text"]["text"]
        == "<@U123123> gained 1 karma."
    )
