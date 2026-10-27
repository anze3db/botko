from unittest.mock import call, create_autospec, patch

import pytest
from freezegun import freeze_time
from slack_sdk.errors import SlackApiError
from slack_sdk.web.client import WebClient

from bot.models import Channel, SlackUser
from bot.slack_cache import refresh_stale_profiles


@pytest.fixture
def client_mock():
    return create_autospec(WebClient, instance=True)


def user_info(display_name):
    return {
        "ok": True,
        "user": {
            "is_bot": False,
            "profile": {
                "display_name": display_name,
                "real_name": f"{display_name} Real",
                "image_192": f"https://example.com/{display_name}.png",
            },
        },
    }


@pytest.mark.django_db
def test_refresh_stale_profiles(client_mock):
    SlackUser.objects.create(slack_id="U1", display_name="U1")
    SlackUser.objects.create(slack_id="U2", display_name="Already known")
    Channel.objects.create(slack_id="C1", name="C1")
    client_mock.users_info.return_value = user_info("alice")
    client_mock.conversations_info.return_value = {
        "ok": True,
        "channel": {"name": "general", "is_private": False},
    }

    refresh_stale_profiles(client_mock)

    client_mock.users_info.assert_called_once_with(user="U1")
    user = SlackUser.objects.get(slack_id="U1")
    assert user.display_name == "alice"
    assert user.real_name == "alice Real"
    assert user.avatar_url == "https://example.com/alice.png"
    assert Channel.objects.get(slack_id="C1").name == "general"


@pytest.mark.django_db
@patch("bot.slack_cache.BATCH_SIZE", 1)
def test_failing_profile_goes_to_the_back(client_mock):
    with freeze_time("2026-01-01"):
        SlackUser.objects.create(slack_id="UGONE", display_name="UGONE")
    with freeze_time("2026-01-02"):
        SlackUser.objects.create(slack_id="U2", display_name="U2")
    client_mock.users_info.side_effect = [
        SlackApiError("user_not_found", {"ok": False, "error": "user_not_found"}),
        user_info("bob"),
    ]

    with freeze_time("2026-01-03"):
        refresh_stale_profiles(client_mock)
        refresh_stale_profiles(client_mock)

    assert client_mock.users_info.call_args_list == [
        call(user="UGONE"),
        call(user="U2"),
    ]
    assert SlackUser.objects.get(slack_id="UGONE").display_name == "UGONE"
    assert SlackUser.objects.get(slack_id="U2").display_name == "bob"
