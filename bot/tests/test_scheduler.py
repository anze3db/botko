import datetime
from datetime import timedelta
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

import freezegun
import pytest
from potatoq import current_app
from potatoq.testing import drain, due, tick
from slack_sdk.web.client import WebClient

from bot import tasks as scheduler
from bot.models import Birthday, Karma
from bot.slack_app import app as slack_app


def test_schedule():
    assert current_app().conf.timezone == "Europe/Lisbon"
    assert "bot.tasks.daily_report" in current_app().tasks
    # 10:00 local time all year round, DST included (naive datetimes are in Lisbon time).
    tz = ZoneInfo("Europe/Lisbon")
    start = datetime.datetime(2026, 3, 28, 12, 0)
    assert due(current_app(), start, start + timedelta(days=2)) == [
        (
            "daily-report",
            datetime.datetime(2026, 3, 29, 10, 0, tzinfo=tz),
        ),  # summer time
        ("daily-report", datetime.datetime(2026, 3, 30, 10, 0, tzinfo=tz)),
    ]


def test_process_timezone():
    assert datetime.datetime.now().astimezone().tzname() == "UTC"


# transaction=True: the broker is the database, and drain() reads the queue on its own
# connection, so it can't see tasks enqueued inside the test's transaction.
@pytest.mark.django_db(transaction=True)
def test_daily_report_runs_at_10():
    app = current_app()
    assert tick(app, at=datetime.datetime(2026, 10, 9, 9, 59, 30)) == []
    assert tick(app, at=datetime.datetime(2026, 10, 9, 10, 0, 1)) == ["daily-report"]

    with patch("bot.tasks.job", autospec=True) as job_mock:
        [task] = drain(app)
    assert (task.name, task.state) == ("bot.tasks.daily_report", "SUCCESS")
    job_mock.assert_called_once_with(slack_app.client)


@freezegun.freeze_time("2022-01-01 10:00:00")
@pytest.mark.django_db
def test_job_no_karma():
    scheduler.job(client_mock := Mock(spec=WebClient()))
    client_mock.chat_postMessage.assert_called()
    assert (
        "Happy New Year"
        in (
            client_mock.chat_postMessage.call_args_list[0][1]["blocks"][0]["text"][
                "text"
            ]
        )
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
        client_mock.chat_postMessage.call_args_list[1][1]["blocks"][2]["text"]["text"]
        == "Nobody received any Karma last month :cry:"
    )


@freezegun.freeze_time("2022-02-01 10:00:00")
@pytest.mark.django_db
def test_job_no_karma_not_in_jan():
    scheduler.job(client_mock := Mock(spec=WebClient()))
    client_mock.chat_postMessage.assert_called()
    assert (
        client_mock.chat_postMessage.call_args_list[0][1]["blocks"][0]["text"]["text"]
        == "Karma stats for January 2022"
    )
    assert (
        client_mock.chat_postMessage.call_args_list[0][1]["blocks"][2]["text"]["text"]
        == "Nobody received any Karma last month :cry:"
    )


@freezegun.freeze_time("2022-01-02 10:00:00")
@pytest.mark.django_db
def test_job_only_on_first():
    scheduler.job(client_mock := Mock(spec=WebClient()))
    client_mock.chat_postMessage.assert_not_called()


@freezegun.freeze_time("2022-01-01 10:00:00")
@pytest.mark.django_db
def test_job_karma():
    now = datetime.datetime.now()
    # Previous day (same month = December 2021)
    Karma.objects.create(
        channel="C02SBSSCMR7",
        ts="1",
        user="U123123",
        created_at=now - timedelta(hours=12),
    )
    Karma.objects.create(
        channel="C02SBSSCMR7",
        ts="1",
        user="U123124",
        created_at=now - timedelta(hours=12),
    )
    # Previous month (November 2021) — shouldn't be in monthly
    Karma.objects.create(
        channel="C02SBSSCMR7",
        ts="2",
        user="U123123",
        created_at=now - timedelta(days=32),
    )
    Karma.objects.create(
        channel="C02SBSSCMR7",
        ts="2",
        user="U123124",
        created_at=now - timedelta(days=32),
    )
    # Current month (January 2022) — shouldn't be in prev month/year
    Karma.objects.create(channel="C02SBSSCMR7", ts="3", user="U123123", created_at=now)
    Karma.objects.create(channel="C02SBSSCMR7", ts="3", user="U123124", created_at=now)

    scheduler.job(client_mock := Mock(spec=WebClient()))
    client_mock.chat_postMessage.assert_called()

    assert (
        client_mock.chat_postMessage.call_args_list[0][1]["blocks"][3]["text"]["text"]
        == "<@U123123> gained 2 karma."
    )
    assert (
        client_mock.chat_postMessage.call_args_list[0][1]["blocks"][4]["text"]["text"]
        == "<@U123124> gained 2 karma."
    )
    assert (
        client_mock.chat_postMessage.call_args_list[1][1]["blocks"][2]["text"]["text"]
        == "<@U123123> gained 1 karma."
    )
    assert (
        client_mock.chat_postMessage.call_args_list[1][1]["blocks"][3]["text"]["text"]
        == "<@U123124> gained 1 karma."
    )


@freezegun.freeze_time("2023-08-07 10:00:00")
@pytest.mark.django_db
def test_birthdays():
    Birthday.objects.create(user="U123123", day=7, month=8)
    scheduler.job(client_mock := Mock(spec=WebClient()))
    client_mock.chat_postMessage.assert_called()
    assert "<@U123123>" in client_mock.chat_postMessage.call_args_list[0][1]["text"]
