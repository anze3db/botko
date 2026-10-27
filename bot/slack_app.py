import logging
import os
import re
from datetime import datetime

from django.core.files.base import ContentFile
from slack_bolt import App
from slack_sdk.web.client import WebClient
from urllib3 import PoolManager

from bot.models import Attachment, Channel, Karma, Message, SlackUser
from bot.utils import KARMA_EMOJIS, parse_karma_from_text

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    token_verification_enabled=False,
)


def _log_message(event: dict) -> Message | None:
    user_slack_id = event.get("user")
    channel_slack_id = event.get("channel")
    if not user_slack_id or not channel_slack_id:
        return None

    slack_user, _ = SlackUser.objects.get_or_create(
        slack_id=user_slack_id,
        defaults={"display_name": user_slack_id},
    )
    channel, _ = Channel.objects.get_or_create(
        slack_id=channel_slack_id,
        defaults={"name": channel_slack_id},
    )

    message, created = Message.objects.update_or_create(
        channel=channel,
        ts=event.get("ts", ""),
        defaults={
            "user": slack_user,
            "text": event.get("text", ""),
            "thread_ts": event.get("thread_ts", ""),
        },
    )

    if created and event.get("files"):
        _process_attachments(message, event["files"])

    return message


def _process_attachments(message: Message, files: list[dict]):
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    if not bot_token:
        return

    http = PoolManager()
    for file_info in files:
        if file_info.get("size", 0) > MAX_FILE_SIZE:
            logger.warning(
                "Skipping large file: %s (%d bytes)",
                file_info.get("name"),
                file_info.get("size"),
            )
            continue

        file_url = file_info.get("url_private_download") or file_info.get("url_private")
        if not file_url:
            continue

        try:
            resp = http.request(
                "GET",
                file_url,
                headers={"Authorization": f"Bearer {bot_token}"},
                timeout=30.0,
            )
            if resp.status != 200:
                logger.warning(
                    "Failed to download file %s: HTTP %d", file_url, resp.status
                )
                continue
        except Exception:
            logger.exception("Failed to download Slack file: %s", file_url)
            continue

        filename = file_info.get("name", "unknown")
        content_type = file_info.get("mimetype", "application/octet-stream")

        attachment = Attachment(
            message=message,
            slack_file_id=file_info.get("id", ""),
            original_url=file_url,
            filename=filename,
            content_type=content_type,
        )
        attachment.file.save(filename, ContentFile(resp.data), save=True)


@app.message(":wave:")
def say_hello(message, say):
    user = message["user"]
    say(f"Hi there, <@{user}>!")


@app.message("karma emojis")
def list_karma_emojis(message, say):
    say(
        "Here are the emojis you can use to give karma:\n"
        + " ".join(f":{emoji}:" for emoji in KARMA_EMOJIS)
    )


@app.message(re.compile(r"\+\+"))
def handle_message_with_karma(client: WebClient, message):
    _log_message(message)

    users = parse_karma_from_text(message.get("text"))
    users_without_current_user = [name for name in users if name != message["user"]]
    if users_without_current_user:
        Karma.give_karma(
            message["channel"],
            message["ts"],
            users_without_current_user,
            giver_slack_id=message["user"],
        )
        client.reactions_add(
            channel=message["channel"], name="botko", timestamp=message["ts"]
        )
    if users != users_without_current_user:
        client.chat_postMessage(
            channel=message["channel"],
            text=f"I can't let you do that <@{message['user']}>. You can't give karma to yourself.",
            thread_ts=message["ts"],
        )


@app.event("reaction_added")
def handle_reaction_added(client: WebClient, event):
    logger.info("Received reaction_added event: %s", event)
    if event["reaction"] in KARMA_EMOJIS and event["item_user"] != event["user"]:
        Karma.give_karma(
            event["item"]["channel"],
            event["item"]["ts"],
            [event["item_user"]],
            giver_slack_id=event["user"],
            emoji=event["reaction"],
        )


@app.event("message")
def handle_message(event):
    subtype = event.get("subtype")
    if subtype is None or subtype == "file_share":
        _log_message(event)


@app.event("app_home_opened")
def update_home_tab(client, event):
    logger.info("Loading home tab for user: %s", event["user"])
    users = list(Karma.leaderboard())
    client.views_publish(
        user_id=event["user"],
        view={
            "type": "home",
            "callback_id": "home_view",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Hey there, <@{event['user']}>! If you'd like to take a look under the hood, my source code is <https://github.com/anze3db/botko|here> :blush:",
                    },
                },
                {"type": "divider"},
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{datetime.now().year} Karma Leaderboard",
                    },
                },
                *[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"<@{user['user']}> has {user['count']} karma.",
                        },
                    }
                    for user in users
                ],
            ],
        },
    )
