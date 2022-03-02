import sqlite3
import time
from datetime import datetime, timedelta

import schedule
from slack_sdk.web.client import WebClient

from app import app
from db import get_connection
from models import fetch_karma_leaderboard_prev_month


def job(connection: sqlite3.Cursor, client: WebClient):
    now = datetime.now()
    prev_month = now.replace(day=1) - timedelta(days=1)

    if now.day != 2:
        # Only report on the first of the month
        return

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
