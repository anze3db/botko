import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

BEFORE = ("bot", "0003_channel_slackuser_karma_channel_ref_message_and_more")
AFTER = ("bot", "0004_backfill_slack_users_and_channels")


def migrate(target):
    executor = MigrationExecutor(connection)
    executor.migrate([target])
    return executor.loader.project_state([target]).apps


@pytest.fixture
def at_0003():
    apps = migrate(BEFORE)
    yield apps
    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())


@pytest.mark.django_db(transaction=True)
def test_backfill_links_karma(at_0003):
    Karma = at_0003.get_model("bot", "Karma")
    SlackUser = at_0003.get_model("bot", "SlackUser")
    known = SlackUser.objects.create(slack_id="UKNOWN", display_name="Known")
    Karma.objects.create(channel="C1", ts="1", user="UKNOWN")
    Karma.objects.create(channel="C1", ts="2", user="UNEW")
    Karma.objects.create(channel="C2", ts="3", user="UNEW")

    apps = migrate(AFTER)

    Karma = apps.get_model("bot", "Karma")
    SlackUser = apps.get_model("bot", "SlackUser")
    Channel = apps.get_model("bot", "Channel")
    assert SlackUser.objects.get(slack_id="UKNOWN").display_name == "Known"
    assert SlackUser.objects.get(slack_id="UNEW").display_name == "UNEW"
    assert sorted(Channel.objects.values_list("slack_id", "name")) == [
        ("C1", "C1"),
        ("C2", "C2"),
    ]
    links = {
        k.ts: (k.receiver.slack_id, k.channel_ref.slack_id)
        for k in Karma.objects.select_related("receiver", "channel_ref")
    }
    assert links == {"1": ("UKNOWN", "C1"), "2": ("UNEW", "C1"), "3": ("UNEW", "C2")}
    assert Karma.objects.get(ts="1").receiver_id == known.pk
