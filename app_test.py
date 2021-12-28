import pytest
from slack_sdk.web.client import WebClient
from app import find_karma, say_hello, update_home_tab
from db import connection_context as db_connection_context

from unittest.mock import Mock, create_autospec

from models import insert_karma


@pytest.fixture
def client_mock():
    return create_autospec(WebClient)


@pytest.fixture
def connection_context():
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
    find_karma(
        client_mock,
        connection_context,
        dict(
            text=text,
            channel="my_channel",
            ts="123",
        ),
    )
    connection = connection_context["connection"]

    assert connection.execute("SELECT COUNT(*) FROM karma").fetchone()[0] == 1, text
    client_mock.reactions_add.assert_called_with(
        channel="my_channel", name="thumbsup", timestamp="123"
    )


@pytest.mark.parametrize(
    "text",
    [
        "Hey there <@U02RW93RGBX>\xa0++ <@U02RMSKJDH>\xa0++",
    ],
)
def test_find_multiple_karma(client_mock, connection_context, text):
    find_karma(
        client_mock,
        connection_context,
        dict(
            text=text,
            channel="my_channel",
            ts="123",
        ),
    )
    connection = connection_context["connection"]

    assert connection.execute("SELECT COUNT(*) FROM karma").fetchone()[0] == 2, text
    client_mock.reactions_add.assert_called_with(
        channel="my_channel", name="thumbsup", timestamp="123"
    )


@pytest.mark.parametrize(
    "text",
    [
        "++",
        "My man++",
        "++Hey there <@U02RW93RGBX>\xa0 thing++ <@U02RMSKJDH>\xa0 other thing++",
    ],
)
def test_find_multiple_karma(client_mock, connection_context, text):
    find_karma(
        client_mock,
        connection_context,
        dict(
            text=text,
            channel="my_channel",
            ts="123",
        ),
    )
    connection = connection_context["connection"]

    assert connection.execute("SELECT COUNT(*) FROM karma").fetchone()[0] == 0, text
    client_mock.reactions_add.assert_not_called()


def test_say_hello():
    say_mock = Mock()
    say_hello(dict(user="123"), say_mock)
    say_mock.assert_called_with("Hi there, <@123>!")


def test_update_home_tab(client_mock, connection_context):
    connection = connection_context["connection"]
    insert_karma(
        connection,
        [
            ("ch1", "11234.123", "U1ASHDJAS"),
            ("ch1", "11234.124", "U1ASHDJAS"),
            ("ch1", "11234.125", "U1ASHDJAS"),
            ("ch1", "11234.126", "U2ASHDJAS"),
            ("ch1", "11234.127", "U2ASHDJAS"),
        ],
    )
    update_home_tab(client_mock, dict(user="123"), connection_context, Mock())
    client_mock.views_publish.assert_called()
