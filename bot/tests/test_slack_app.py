from datetime import datetime, timedelta
from unittest.mock import Mock, create_autospec

import pytest
from slack_sdk.web.client import WebClient

from bot.models import Karma
from bot.slack_app import handle_message_with_karma, say_hello, update_home_tab


@pytest.fixture(name="client_mock")
def fixture_client_mock():
    return create_autospec(WebClient)


@pytest.mark.parametrize(
    "text",
    [
        "Hey there <@U02RW93RGBX>\xa0++",
        "Wow, <@U02RW93RGBX> ++",
        "Amazing, <@U02RW93RGBX>++",
    ],
)
@pytest.mark.django_db
def test_find_karma(client_mock, text):
    handle_message_with_karma(
        client_mock,
        dict(
            text=text,
            channel="my_channel",
            ts="123",
            user="U2RMSKJDH",
        ),
    )

    assert Karma.objects.count() == 1, text
    client_mock.reactions_add.assert_called_with(
        channel="my_channel", name="botko", timestamp="123"
    )
    client_mock.chat_postMessage.assert_not_called()


@pytest.mark.django_db
def test_find_multiple_karma(client_mock):
    handle_message_with_karma(
        client_mock,
        dict(
            text="Hey there <@U02RW93RGBX>\xa0++ <@U02RMSKJDH>\xa0++",
            channel="my_channel",
            ts="123",
            user="U2RMSKJDH",
        ),
    )

    assert Karma.objects.count() == 2
    client_mock.reactions_add.assert_called_with(
        channel="my_channel", name="botko", timestamp="123"
    )
    client_mock.chat_postMessage.assert_not_called()


@pytest.mark.parametrize(
    "text",
    [
        "++",
        "My man+++++",
        "++Hey there <@U02RW93RGBX>\xa0 thing++ <@U02RMSKJDH>\xa0 other thing++",
    ],
)
@pytest.mark.django_db
def test_find_multiple_invalid_karma(client_mock, text):
    handle_message_with_karma(
        client_mock,
        dict(
            text=text,
            channel="my_channel",
            ts="123",
            user="U2RMSKJDH",
        ),
    )

    assert Karma.objects.count() == 0, text
    client_mock.reactions_add.assert_not_called()
    client_mock.chat_postMessage.assert_not_called()


@pytest.mark.django_db
def test_self_karma(client_mock):
    handle_message_with_karma(
        client_mock,
        dict(
            text="I am giving <@U02RMSKJDH>++",
            channel="my_channel",
            ts="123",
            user="U02RMSKJDH",
        ),
    )

    assert Karma.objects.count() == 0
    client_mock.reactions_add.assert_not_called()
    client_mock.chat_postMessage.assert_called_with(
        channel="my_channel",
        text="I can't let you do that <@U02RMSKJDH>. You can't give karma to yourself.",
        thread_ts="123",
    )


@pytest.mark.django_db
def test_self_karma_and_other_karma(client_mock):
    handle_message_with_karma(
        client_mock,
        dict(
            text="I am giving <@U02RMSKJDH>++ <@UOTHRUSR>++ ",
            channel="my_channel",
            ts="123",
            user="U02RMSKJDH",
        ),
    )

    assert Karma.objects.count() == 1
    client_mock.reactions_add.assert_called_with(
        channel="my_channel", name="botko", timestamp="123"
    )
    client_mock.chat_postMessage.assert_called_with(
        channel="my_channel",
        text="I can't let you do that <@U02RMSKJDH>. You can't give karma to yourself.",
        thread_ts="123",
    )


def test_say_hello():
    say_mock = Mock()
    say_hello(dict(user="123"), say_mock)
    say_mock.assert_called_with("Hi there, <@123>!")


@pytest.mark.django_db
def test_update_home_tab(client_mock: Mock):
    now = datetime.now()
    # Old karma — outside current year, should not appear
    Karma.objects.create(
        channel="C02SBSSCMR7",
        ts="old",
        user="U123123",
        created_at=now - timedelta(days=700),
    )
    # Current year karma
    Karma.give_karma(
        "C02SBSSCMR7",
        "new",
        ["U02RW93RGBX", "U02RW93RGBX", "U6LJ2A03A", "U6LJ2A03A", "U6LJ2A03A"],
    )

    update_home_tab(client=client_mock, event=dict(user="123"))
    client_mock.views_publish.assert_called()
    view = client_mock.views_publish.call_args.kwargs["view"]
    assert view["type"] == "home"
    assert f"{datetime.now().year} Karma Leaderboard" in str(view["blocks"])
    assert "<@U6LJ2A03A> has 3 karma." in str(view["blocks"])
    assert "<@U02RW93RGBX> has 2 karma." in str(view["blocks"])
    assert "<@U123123> has 1 karma." not in str(view["blocks"])
