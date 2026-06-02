import logging

from django.db.models import F
from slack_sdk.errors import SlackApiError
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler
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
    # Ensure client has rate limit retry handler
    if not any(isinstance(h, RateLimitErrorRetryHandler) for h in client.retry_handlers):
        client.retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=3))

    # Process users in batches
    stale_users = SlackUser.objects.filter(display_name=F("slack_id"))[:BATCH_SIZE]
    for user in stale_users:
        try:
            refresh_user(user.slack_id, client)
        except SlackApiError as e:
            logger.error("Slack API error refreshing user %s: %s", user.slack_id, e)
        except Exception:
            logger.exception("Unexpected error refreshing user %s", user.slack_id)

    # Process channels in batches
    stale_channels = Channel.objects.filter(name=F("slack_id"))[:BATCH_SIZE]
    for channel in stale_channels:
        try:
            refresh_channel(channel.slack_id, client)
        except SlackApiError as e:
            logger.error("Slack API error refreshing channel %s: %s", channel.slack_id, e)
        except Exception:
            logger.exception("Unexpected error refreshing channel %s", channel.slack_id)
