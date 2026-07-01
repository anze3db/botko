from datetime import datetime

import pytest
from django.db import IntegrityError

from bot.models import Attachment, Channel, Karma, Message, SlackUser


@pytest.mark.django_db
def test_slack_user_create():
    user = SlackUser.objects.create(slack_id="U123", display_name="testuser")
    assert user.slack_id == "U123"
    assert str(user) == "testuser (U123)"


@pytest.mark.django_db
def test_slack_user_unique():
    SlackUser.objects.create(slack_id="U123")
    with pytest.raises(IntegrityError):
        SlackUser.objects.create(slack_id="U123")


@pytest.mark.django_db
def test_channel_create():
    channel = Channel.objects.create(slack_id="C123", name="general")
    assert channel.slack_id == "C123"
    assert str(channel) == "#general (C123)"


@pytest.mark.django_db
def test_message_create():
    user = SlackUser.objects.create(slack_id="U123")
    channel = Channel.objects.create(slack_id="C123")
    msg = Message.objects.create(channel=channel, user=user, ts="123.456", text="hello")
    assert msg.text == "hello"
    assert msg.user == user
    assert msg.channel == channel


@pytest.mark.django_db
def test_message_unique_constraint():
    user = SlackUser.objects.create(slack_id="U123")
    channel = Channel.objects.create(slack_id="C123")
    Message.objects.create(channel=channel, user=user, ts="123.456")
    with pytest.raises(IntegrityError):
        Message.objects.create(channel=channel, user=user, ts="123.456")


@pytest.mark.django_db
def test_attachment_create(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    user = SlackUser.objects.create(slack_id="U123")
    channel = Channel.objects.create(slack_id="C123")
    msg = Message.objects.create(channel=channel, user=user, ts="1.0", text="pic")
    att = Attachment.objects.create(
        message=msg,
        slack_file_id="F123",
        filename="test.png",
        content_type="image/png",
    )
    assert att.message == msg
    assert att.filename == "test.png"
    assert msg.attachments.count() == 1


@pytest.mark.django_db
def test_karma_with_giver():
    SlackUser.objects.create(slack_id="UGIVER", display_name="Giver")
    SlackUser.objects.create(slack_id="URECEIVER", display_name="Receiver")
    Channel.objects.create(slack_id="C123")
    Karma.give_karma("C123", "ts1", ["URECEIVER"], giver_slack_id="UGIVER")
    k = Karma.objects.first()
    assert k.giver.slack_id == "UGIVER"
    assert k.receiver.slack_id == "URECEIVER"
    assert k.channel_ref.slack_id == "C123"


@pytest.mark.django_db
def test_karma_without_giver_backward_compat():
    Karma.give_karma("C123", "ts1", ["URECEIVER"])
    k = Karma.objects.first()
    assert k.giver is None
    assert k.user == "URECEIVER"
    assert k.receiver is not None


@pytest.mark.django_db
def test_karma_with_emoji():
    Karma.give_karma(
        "C123", "ts1", ["URECEIVER"], giver_slack_id="UGIVER", emoji="fire"
    )
    k = Karma.objects.first()
    assert k.emoji == "fire"


@pytest.mark.django_db
def test_karma_links_to_message():
    user = SlackUser.objects.create(slack_id="UAUTHOR")
    channel = Channel.objects.create(slack_id="C123")
    msg = Message.objects.create(
        channel=channel, user=user, ts="ts1", text="great post"
    )
    Karma.give_karma("C123", "ts1", ["UAUTHOR"], giver_slack_id="UGIVER")
    k = Karma.objects.first()
    assert k.message == msg


@pytest.mark.django_db
def test_giver_leaderboard():
    giver = SlackUser.objects.create(slack_id="UGIVER", display_name="Giver")
    Channel.objects.create(slack_id="C1")
    for i in range(5):
        Karma.objects.create(channel="C1", ts=f"t{i}", user="URECEIVER", giver=giver)
    lb = list(Karma.giver_leaderboard())
    assert lb[0]["count"] == 5
    assert lb[0]["giver__slack_id"] == "UGIVER"


@pytest.mark.django_db
def test_top_messages():
    user = SlackUser.objects.create(slack_id="U1")
    channel = Channel.objects.create(slack_id="C1")
    msg = Message.objects.create(channel=channel, user=user, ts="1", text="Great post!")
    for i in range(3):
        Karma.objects.create(channel="C1", ts="1", user="U1", message=msg)
    top = list(Karma.top_messages(limit=10))
    assert top[0]["karma_count"] == 3
