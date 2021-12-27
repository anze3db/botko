import pytest
from slack_sdk.web.client import WebClient
from app import find_karma, say_hello, update_home_tab
from unittest.mock import Mock, create_autospec


@pytest.fixture
def client_mock():
    return create_autospec(WebClient)


@pytest.mark.parametrize(
    "text",
    [
        "Hey there <@U02RW93RGBX>\xa0++",
        "Wow, thing++",
        "Amazing, thing ++",
    ],
)
def test_find_karma(client_mock, text):
    find_karma(
        client_mock,
        dict(
            text=text,
            channel="my_channel",
            ts="123",
        ),
    )
    client_mock.reactions_add.assert_called_with(
        channel="my_channel", name="thumbsup", timestamp="123"
    )


def test_say_hello():
    say_mock = Mock()
    say_hello(dict(user="123"), say_mock)
    say_mock.assert_called_with("Hi there, <@123>!")


def test_update_home_tab(client_mock):
    update_home_tab(client_mock, dict(user="123"), Mock())
    client_mock.views_publish.assert_called()
