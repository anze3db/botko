import os
import re

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.starlette import SlackRequestHandler
from slack_sdk.web.client import WebClient
from starlette.applications import Starlette
from starlette.routing import Route

from db import connection_context
from models import karma_leaderboard, parse_karma_from_text

load_dotenv()


app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)


@app.message(":wave:")
def say_hello(message, say):
    user = message["user"]
    say(f"Hi there, <@{user}>!")


@app.message(re.compile(r"\+\+"), middleware=[connection_context])
def find_karma(client: WebClient, context, message):
    if parse_karma_from_text(message, context["connection"]):
        client.reactions_add(
            channel=message["channel"], name="thumbsup", timestamp=message["ts"]
        )


@app.event("app_home_opened", middleware=[connection_context])
def update_home_tab(client, event, context, logger):

    users = karma_leaderboard(context["connection"])
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


# Start your app


app_handler = SlackRequestHandler(app)


async def endpoint(req):
    return await app_handler.handle(req)


api = Starlette(
    debug=True, routes=[Route("/slack/events", endpoint=endpoint, methods=["POST"])]
)
