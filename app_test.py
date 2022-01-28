import time
from datetime import datetime
from unittest.mock import Mock, create_autospec

import pytest
from slack_sdk.web.client import WebClient

from app import handle_message_with_karma, say_hello, update_home_tab
from db import connection_context as db_connection_context
from models import insert_karma


@pytest.fixture(name="client_mock")
def fixture_client_mock():
    return create_autospec(WebClient)


@pytest.fixture(name="connection_context")
def fixture_connection_context():
    db_connection_context(context := {}, lambda: None)
    connection = context["connection"]
    connection.execute("BEGIN")
    yield context
    connection.execute("ROLLBACK")


@pytest.mark.parametrize(
    "text",
    [
        "Hey there <@U02RW93RGBX>\xa0++",
        "Wow, <@U02RW93RGBX> ++",
        "Amazing, <@U02RW93RGBX>++",
    ],
)
def test_find_karma(client_mock, connection_context, text):
    handle_message_with_karma(
        client_mock,
        connection_context,
        dict(
            text=text,
            channel="my_channel",
            ts="123",
            user="U2RMSKJDH",
        ),
    )
    connection = connection_context["connection"]

    assert connection.execute("SELECT COUNT(*) FROM karma").fetchone()[0] == 1, text
    client_mock.reactions_add.assert_called_with(
        channel="my_channel", name="botko", timestamp="123"
    )
    client_mock.chat_postMessage.assert_not_called()


def test_find_multiple_karma(client_mock, connection_context):
    handle_message_with_karma(
        client_mock,
        connection_context,
        dict(
            text="Hey there <@U02RW93RGBX>\xa0++ <@U02RMSKJDH>\xa0++",
            channel="my_channel",
            ts="123",
            user="U2RMSKJDH",
        ),
    )
    connection = connection_context["connection"]

    assert connection.execute("SELECT COUNT(*) FROM karma").fetchone()[0] == 2
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
def test_find_multiple_invalid_karma(client_mock, connection_context, text):
    handle_message_with_karma(
        client_mock,
        connection_context,
        dict(
            text=text,
            channel="my_channel",
            ts="123",
            user="U2RMSKJDH",
        ),
    )
    connection = connection_context["connection"]

    assert connection.execute("SELECT COUNT(*) FROM karma").fetchone()[0] == 0, text
    client_mock.reactions_add.assert_not_called()
    client_mock.chat_postMessage.assert_not_called()


def test_self_karma(client_mock, connection_context):
    handle_message_with_karma(
        client_mock,
        connection_context,
        dict(
            text="I am giving <@U02RMSKJDH>++",
            channel="my_channel",
            ts="123",
            user="U02RMSKJDH",
        ),
    )
    connection = connection_context["connection"]

    assert connection.execute("SELECT COUNT(*) FROM karma").fetchone()[0] == 0
    client_mock.reactions_add.assert_not_called()
    client_mock.chat_postMessage.assert_called_with(
        channel="my_channel",
        text="I can't let you do that <@U02RMSKJDH>. You can't give karma to yourself.",
        thread_ts="123",
    )


def test_self_karma_and_other_karma(client_mock, connection_context):
    handle_message_with_karma(
        client_mock,
        connection_context,
        dict(
            text="I am giving <@U02RMSKJDH>++ <@UOTHRUSR>++ ",
            channel="my_channel",
            ts="123",
            user="U02RMSKJDH",
        ),
    )
    connection = connection_context["connection"]

    assert connection.execute("SELECT COUNT(*) FROM karma").fetchone()[0] == 1
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


def test_update_home_tab(client_mock: Mock, connection_context):
    connection = connection_context["connection"]
    insert_karma(
        connection,
        channel="C02SBSSCMR7",
        ts=f"{time.time()-60*60*60*24*700}",
        users=["U123123"],
    )
    insert_karma(
        connection,
        channel="C02SBSSCMR7",
        ts=f"{time.time()}",
        users=["U02RW93RGBX", "U02RW93RGBX", "U6LJ2A03A", "U6LJ2A03A", "U6LJ2A03A"],
    )
    update_home_tab(
        client=client_mock, event=dict(user="123"), context=connection_context
    )
    client_mock.views_publish.assert_called()
    view = client_mock.views_publish.call_args.kwargs["view"]
    assert view["type"] == "home"
    assert f"{datetime.now().year} Karma Leaderboard" in str(view["blocks"])
    assert "<@U6LJ2A03A> has 3 karma." in str(view["blocks"])
    assert "<@U02RW93RGBX> has 2 karma." in str(view["blocks"])
    assert "<@U123123> has 1 karma." not in str(view["blocks"])
