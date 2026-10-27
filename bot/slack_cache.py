import logging
from collections.abc import Callable

from django.db.models import F
from slack_sdk.errors import SlackApiError
from slack_sdk.web.client import WebClient

from bot.models import Channel, SlackUser

logger = logging.getLogger(__name__)

# Maximum number of stale profiles to refresh per run
BATCH_SIZE = 20


def refresh_user(slack_id: str, client: WebClient) -> SlackUser | None:
    resp = client.users_info(user=slack_id)
    if resp["ok"]:
        profile = resp["user"]["profile"]
        user, _ = SlackUser.objects.update_or_create(
            slack_id=slack_id,
            defaults={
                "display_name": profile.get("display_name")
                or profile.get("real_name", ""),
                "real_name": profile.get("real_name", ""),
                "avatar_url": profile.get("image_192", ""),
                "is_bot": resp["user"].get("is_bot", False),
            },
        )
        return user
    return None


def refresh_channel(slack_id: str, client: WebClient) -> Channel | None:
    resp = client.conversations_info(channel=slack_id)
    if resp["ok"]:
        channel_data = resp["channel"]
        channel, _ = Channel.objects.update_or_create(
            slack_id=slack_id,
            defaults={
                "name": channel_data.get("name", ""),
                "is_private": channel_data.get("is_private", False),
            },
        )
        return channel
    return None


def refresh_stale_profiles(client: WebClient):
    # Oldest first, so profiles that keep failing don't crowd out the rest
    stale_users = SlackUser.objects.filter(display_name=F("slack_id")).order_by(
        "updated_at"
    )[:BATCH_SIZE]
    for user in stale_users:
        _refresh_or_requeue(user, refresh_user, client)

    stale_channels = Channel.objects.filter(name=F("slack_id")).order_by("updated_at")[
        :BATCH_SIZE
    ]
    for channel in stale_channels:
        _refresh_or_requeue(channel, refresh_channel, client)


def _refresh_or_requeue(
    obj: SlackUser | Channel,
    refresh: Callable[[str, WebClient], object],
    client: WebClient,
):
    try:
        refresh(obj.slack_id, client)
        return
    except SlackApiError as e:
        logger.error("Slack API error refreshing %s: %s", obj.slack_id, e)
    except Exception:
        logger.exception("Unexpected error refreshing %s", obj.slack_id)
    # Bump updated_at to move it behind the other stale rows for the next run
    obj.save(update_fields=["updated_at"])
