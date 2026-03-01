import logging
import os
import re
from datetime import datetime

from slack_bolt import App
from slack_sdk.web.client import WebClient

from bot.models import Karma
from bot.utils import KARMA_EMOJIS, parse_karma_from_text

logger = logging.getLogger(__name__)

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    token_verification_enabled=False,
)


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
    users = parse_karma_from_text(message.get("text"))
    users_without_current_user = [name for name in users if name != message["user"]]
    if users_without_current_user:
        Karma.give_karma(
            message["channel"],
            message["ts"],
            users_without_current_user,
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
        )


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
