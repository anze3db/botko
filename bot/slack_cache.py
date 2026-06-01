import logging

from django.db.models import F
from slack_sdk.web.client import WebClient

from bot.models import Channel, SlackUser

logger = logging.getLogger(__name__)


def refresh_user(slack_id: str, client: WebClient) -> SlackUser | None:
    try:
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
    except Exception:
        logger.exception("Failed to fetch user info for %s", slack_id)
    return None


def refresh_channel(slack_id: str, client: WebClient) -> Channel | None:
    try:
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
    except Exception:
        logger.exception("Failed to fetch channel info for %s", slack_id)
    return None


def refresh_stale_profiles(client: WebClient):
    for user in SlackUser.objects.filter(display_name=F("slack_id")):
        refresh_user(user.slack_id, client)

    for channel in Channel.objects.filter(name=F("slack_id")):
        refresh_channel(channel.slack_id, client)
