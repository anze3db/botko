import pytest
from django.test import RequestFactory

from bot.models import Channel, Karma, Message, SlackUser
from bot.views import index, top_givers, top_posts, top_receivers


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
def test_index_view(rf):
    response = index(rf.get("/"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_index_view_with_data(rf):
    Karma.give_karma("C1", "t1", ["U123"])
    response = index(rf.get("/"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_top_receivers_view(rf):
    Karma.give_karma("C1", "t1", ["U123"])
    response = top_receivers(rf.get("/receivers/"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_top_receivers_empty(rf):
    response = top_receivers(rf.get("/receivers/"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_top_givers_view(rf):
    Karma.give_karma("C1", "t1", ["U123"], giver_slack_id="UGIVER")
    response = top_givers(rf.get("/givers/"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_top_givers_empty(rf):
    response = top_givers(rf.get("/givers/"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_top_posts_view(rf):
    user = SlackUser.objects.create(slack_id="UAUTHOR", display_name="Author")
    channel = Channel.objects.create(slack_id="C1", name="general")
    msg = Message.objects.create(channel=channel, user=user, ts="1.0", text="cool post")
    Karma.objects.create(
        channel="C1", ts="1.0", user="UAUTHOR", message=msg, emoji="fire"
    )
    response = top_posts(rf.get("/posts/"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_top_posts_empty(rf):
    response = top_posts(rf.get("/posts/"))
    assert response.status_code == 200
