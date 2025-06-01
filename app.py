import os
import re
from datetime import datetime

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.starlette import SlackRequestHandler
from slack_sdk.web.client import WebClient
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from db import get_connection
from models import fetch_karma_leaderboard, insert_karma, parse_karma_from_text

load_dotenv()

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    token_verification_enabled=False,
)

KARMA_EMOJIS = (
    "botko",
    "100",
    "1000",
    "+1",
    "thumbs",
    "thumbsup_all",
    "heavy_plus_sign::laughing",
    "joy",
    "rolling_on_the_floor_laughing",
    "joy_cat",
    "smile",
    "smiling_face_with_3_hearts",
    "heart",
    "hearts",
    "lolsob",
    "fire",
    "rocket",
    "tada",
    "face_holding_back_tears",
)


@app.message(":wave:")
def say_hello(message, say):
    user = message["user"]
    say(f"Hi there, <@{user}>!")


@app.message("karma emojis")
def list_karma_emojis(message, say):
    say(
        "Here are the emojis you can use to give karma:\n"
        + "\n".join(f":{emoji}:" for emoji in KARMA_EMOJIS)
    )


@app.message(re.compile(r"\+\+"))
def handle_message_with_karma(client: WebClient, message):
    users = parse_karma_from_text(message.get("text"))
    users_without_current_user = [name for name in users if name != message["user"]]
    if users_without_current_user:
        with get_connection() as cursor:
            insert_karma(
                cursor,
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
    if event["reaction"] in KARMA_EMOJIS and event["item_user"] != event["user"]:
        with get_connection() as cursor:
            insert_karma(
                cursor,
                event["item"]["channel"],
                event["item"]["ts"],
                [event["user"]],
            )


@app.event("app_home_opened")
def update_home_tab(client, event):
    with get_connection() as cursor:
        users = list(fetch_karma_leaderboard(cursor))
    client.views_publish(
        user_id=event["user"],
        view={
            "type": "home",
            "callback_id": "home_view",
            # body of the view
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


app_handler = SlackRequestHandler(app)


async def endpoint(req):
    return await app_handler.handle(req)


def heartbeat(_):
    return PlainTextResponse("Hello 🤖")


api = Starlette(
    debug=os.environ.get("DEBUG", "") == "True",
    routes=[
        Route("/slack/events", endpoint=endpoint, methods=["POST"]),
        Route("/", endpoint=heartbeat, methods=["GET"]),
    ],
)

if sentry_dns := os.environ.get("SENTRY_DNS"):
    import logging

    import sentry_sdk
    from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

    logger = logging.getLogger("uvicorn.app")

    logger.info("👩‍🚒 Setting up Sentry")

    sentry_sdk.init(  # pylint: disable=abstract-class-instantiated
        sentry_dns,
        traces_sample_rate=0.1,
    )
    api = SentryAsgiMiddleware(api)
