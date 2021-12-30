import os
import re

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.starlette import SlackRequestHandler
from slack_sdk.web.client import WebClient
from starlette.applications import Starlette
from starlette.routing import Route

load_dotenv()  # Needs to be run before we import db

from db import connection_context
from models import fetch_karma_leaderboard, insert_karma, parse_karma_from_text

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)


@app.message(":wave:")
def say_hello(message, say):
    user = message["user"]
    say(f"Hi there, <@{user}>!")


@app.message(re.compile(r"\+\+"), middleware=[connection_context])
def handle_message_with_karma(client: WebClient, context, message):
    users = parse_karma_from_text(message.get("text"))
    users_without_current_user = [name for name in users if name != message["user"]]
    if users_without_current_user:
        insert_karma(
            context["connection"],
            message["channel"],
            message["ts"],
            users_without_current_user,
        )
        client.reactions_add(
            channel=message["channel"], name="botko", timestamp=message["ts"]
        )


@app.event("app_home_opened", middleware=[connection_context])
def update_home_tab(client, event, context, logger):

    users = fetch_karma_leaderboard(context["connection"])
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
                        "text": f"Hey there, <@{event['user']}>!",
                    },
                },
                {"type": "divider"},
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


api = Starlette(
    debug=os.environ.get("DEBUG", "") == "True",
    routes=[Route("/slack/events", endpoint=endpoint, methods=["POST"])],
)
