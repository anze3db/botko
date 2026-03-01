import datetime
from datetime import timedelta
from unittest.mock import Mock

import freezegun
import pytest
from slack_sdk.web.client import WebClient

import scheduler
from bot.models import Birthday, Karma


def test_schedule():
    assert [(job.at_time, job.interval) for job in scheduler.schedule.get_jobs()] == [
        (datetime.time(10, 0), 1)
    ]


@freezegun.freeze_time("2022-01-01 10:00:00")
@pytest.mark.django_db
def test_job_no_karma():
    scheduler.job(client_mock := Mock(spec=WebClient()))
    client_mock.chat_postMessage.assert_called()
    assert "Happy New Year" in (
        client_mock.chat_postMessage.call_args_list[0][1]["blocks"][0]["text"]["text"]
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
@pytest.mark.django_db
def test_job_no_karma_not_in_jan():
    scheduler.job(client_mock := Mock(spec=WebClient()))
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
@pytest.mark.django_db
def test_job_only_on_first():
    scheduler.job(client_mock := Mock(spec=WebClient()))
    client_mock.chat_postMessage.assert_not_called()


@freezegun.freeze_time("2022-01-01 10:00:00")
@pytest.mark.django_db
def test_job_karma():
    now = datetime.datetime.now()
    # Previous day (same month = December 2021)
    Karma.objects.create(channel="C02SBSSCMR7", ts="1", user="U123123", created_at=now - timedelta(hours=12))
    Karma.objects.create(channel="C02SBSSCMR7", ts="1", user="U123124", created_at=now - timedelta(hours=12))
    # Previous month (November 2021) — shouldn't be in monthly
    Karma.objects.create(channel="C02SBSSCMR7", ts="2", user="U123123", created_at=now - timedelta(days=32))
    Karma.objects.create(channel="C02SBSSCMR7", ts="2", user="U123124", created_at=now - timedelta(days=32))
    # Current month (January 2022) — shouldn't be in prev month/year
    Karma.objects.create(channel="C02SBSSCMR7", ts="3", user="U123123", created_at=now)
    Karma.objects.create(channel="C02SBSSCMR7", ts="3", user="U123124", created_at=now)

    scheduler.job(client_mock := Mock(spec=WebClient()))
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


@freezegun.freeze_time("2023-08-07 10:00:00")
@pytest.mark.django_db
def test_birthdays():
    Birthday.objects.create(user="U123123", day=7, month=8)
    scheduler.job(client_mock := Mock(spec=WebClient()))
    client_mock.chat_postMessage.assert_called()
    assert "<@U123123>" in client_mock.chat_postMessage.call_args_list[0][1]["text"]
