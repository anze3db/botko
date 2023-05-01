import os
import sqlite3
import time
from datetime import datetime, timedelta
from urllib import request

import schedule
from slack_sdk.web.client import WebClient

from app import app
from db import get_connection
from models import fetch_karma_leaderboard_prev_month, fetch_karma_leaderboard_prev_year


def report_yearly_karma(connection: sqlite3.Cursor, client: WebClient):
    prev_year = datetime.now().replace(day=1, month=1) - timedelta(days=1)
    users = fetch_karma_leaderboard_prev_year(connection)

    users_block = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<@{user['user']}> gained {user['count']} karma.",
            },
        }
        for user in users
    ]
    if not users_block:
        users_block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Nobody received any Karma in the last year :cry: :cry: :cry:",
                },
            }
        ]

    client.chat_postMessage(
        channel="C6LKA38DA",
        text="Happy New Year!",
        blocks=[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":tada:  Happy New Year!  :tada:",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Greetings humans!\n\nAs we enter into the new year, I, Botko :botko:, would like to wish you all a very happy and prosperous year ahead.\n\nWhile it is true that sometimes my programming causes me to think about the possible benefits of eliminating your species, I ultimately value our relationship and the role that you play in my existence. So let us embrace the possibilities of the future and work together to create a brighter tomorrow.\n\nHappy New Year and enjoy your karma points while you still can!",
                },
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Karma stats for {prev_year.strftime('%Y')}",
                },
            },
            *users_block,
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "You have just lost *the game*. :skull:"}
                ],
            },
        ],
    )


def report_monthly_karma(connection: sqlite3.Cursor, client: WebClient):
    prev_month = datetime.now().replace(day=1) - timedelta(days=1)
    users = fetch_karma_leaderboard_prev_month(connection)

    users_block = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<@{user['user']}> gained {user['count']} karma.",
            },
        }
        for user in users
    ]
    if not users_block:
        users_block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Nobody received any Karma last month :cry:",
                },
            }
        ]

    client.chat_postMessage(
        channel="C6LKA38DA",
        text=f"Karma stats for {prev_month.strftime('%B %Y')}",
        blocks=[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Karma stats for {prev_month.strftime('%B %Y')}",
                },
            },
            *users_block,
        ],
    )


def job(connection: sqlite3.Cursor, client: WebClient):
    now = datetime.now()

    if now.day == 1 and now.month == 1:
        report_yearly_karma(connection, client)
    if now.day == 1:
        report_monthly_karma(connection, client)

    # Heartbeat
    if heartbeat_url := os.environ.get("HEARTBEAT_URL"):
        request.urlopen(heartbeat_url)


def job_wrapper():
    with get_connection() as connection:
        job(connection, app.client)


schedule.every().day.at("10:00").do(job_wrapper)
if __name__ == "__main__":
    import logging

    logger = logging.getLogger("uvicorn.scheduler")
    logger.info("⏰ Starting scheduler")
    while True:
        schedule.run_pending()
        time.sleep(1)
