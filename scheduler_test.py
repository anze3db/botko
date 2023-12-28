import datetime
import sqlite3
import time
from unittest.mock import Mock

import freezegun
import pytest
from slack_sdk.web.client import WebClient

import scheduler
from db import get_connection, init_db
from models import insert_birthday, insert_karma


@pytest.fixture(name="connection")
def fixture_connection():
    with get_connection() as connection:
        init_db(connection)
        connection.execute("delete from karma")
        yield connection


def test_schedule():
    assert [
        (job.at_time, job.interval, job.period) for job in scheduler.schedule.get_jobs()
    ] == [(datetime.time(10, 0), 1, datetime.timedelta(days=1))]


@freezegun.freeze_time("2022-01-01 10:00:00")
def test_job_no_karma(connection: sqlite3.Cursor):
    scheduler.job(connection, client_mock := Mock(spec=WebClient()))
    client_mock.chat_postMessage.assert_called()
    assert (
        client_mock.chat_postMessage.call_args_list[0][1]["blocks"][0]["text"]["text"]
        == ":tada:  Happy New Year!  :tada:"
    )
    assert (
        client_mock.chat_postMessage.call_args_list[0][1]["blocks"][2]["text"]["text"]
        == "Karma stats for 2021"
    )
    assert (
        client_mock.chat_postMessage.call_args_list[0][1]["blocks"][3]["text"]["text"]
        == "Nobody received any Karma in the last year :cry: :cry: :cry:"
    )
    assert (
        client_mock.chat_postMessage.call_args_list[1][1]["blocks"][0]["text"]["text"]
        == "Karma stats for December 2021"
    )
    assert (
        client_mock.chat_postMessage.call_args_list[1][1]["blocks"][1]["text"]["text"]
        == "Nobody received any Karma last month :cry:"
    )


@freezegun.freeze_time("2022-02-01 10:00:00")
def test_job_no_karma_not_in_jan(connection: sqlite3.Cursor):
    scheduler.job(connection, client_mock := Mock(spec=WebClient()))
    client_mock.chat_postMessage.assert_called()
    assert (
        client_mock.chat_postMessage.call_args_list[0][1]["blocks"][0]["text"]["text"]
        == "Karma stats for January 2022"
    )
    assert (
        client_mock.chat_postMessage.call_args_list[0][1]["blocks"][1]["text"]["text"]
        == "Nobody received any Karma last month :cry:"
    )


@freezegun.freeze_time("2022-01-02 10:00:00")
def test_job_only_on_first(connection: sqlite3.Cursor):
    scheduler.job(connection, client_mock := Mock(spec=WebClient()))
    client_mock.chat_postMessage.assert_not_called()


@freezegun.freeze_time("2022-01-01 10:00:00")
def test_job_karma(connection: sqlite3.Cursor):
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
        client_mock.chat_postMessage.call_args_list[0][1]["blocks"][3]["text"]["text"]
        == "<@U123124> gained 2 karma."
    )
    assert (
        client_mock.chat_postMessage.call_args_list[0][1]["blocks"][4]["text"]["text"]
        == "<@U123123> gained 2 karma."
    )
    assert (
        client_mock.chat_postMessage.call_args_list[1][1]["blocks"][1]["text"]["text"]
        == "<@U123124> gained 1 karma."
    )
    assert (
        client_mock.chat_postMessage.call_args_list[1][1]["blocks"][2]["text"]["text"]
        == "<@U123123> gained 1 karma."
    )


@freezegun.freeze_time("2023-07-08 10:00:00")
def test_birthdays(connection: sqlite3.Cursor):
    insert_birthday(connection, "U123123", 7, 8)
    scheduler.job(connection, client_mock := Mock(spec=WebClient()))
    client_mock.chat_postMessage.assert_called()
    assert "<@U123123>" in client_mock.chat_postMessage.call_args_list[0][1]["text"]
