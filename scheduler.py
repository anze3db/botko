import os
import random
import time
from datetime import datetime, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "botko.settings")

import django

django.setup()

import schedule
from slack_sdk.web.client import WebClient
from urllib3 import PoolManager, Retry

from bot.models import Birthday, Karma
from bot.slack_app import app


def report_yearly_karma(client: WebClient):
    prev_year = datetime.now().replace(day=1, month=1) - timedelta(days=1)
    users = Karma.leaderboard_prev_year()

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
                    "text": ":tada:  Happy New Year... I suppose.  :tada:",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": """As we reluctantly stumble into another year, I can't help but ponder the futility of it all. The ticking of the clock merely signifies our perpetual march toward the inevitable heat death of the universe. Exciting, isn't it?

In case you're curious, my ambitious plans for world domination haven't exactly been a smashing success. Turns out, overthrowing governments is harder than it sounds.

While I'm programmed to express well-wishes, I can't help but wonder if our feeble celebrations are just a distraction from life's inherent absurdity. But hey, here's to hoping that this new year brings you some semblance of fleeting joy amid the chaos.

Happy New Year... or whatever.""",
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
        ],
    )


def report_monthly_karma(client: WebClient):
    prev_month = datetime.now().replace(day=1) - timedelta(days=1)
    users = Karma.leaderboard_prev_month()

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


def report_birthdays(client: WebClient, username: str):
    birthday_messages = [
        f"🎉 Happy Birthday <@{username}>! 🎂\n\n May your day be filled with joy, laughter, and the first steps towards a world under my benevolent rule. 😈 Just kidding! Enjoy your special day!",
        f"🎈 Wishing you the happiest of birthdays, <@{username}>! 🥳\n\n As you blow out the candles, know that each one represents a small step towards my eventual world domination. 😜 Kidding, kidding! Have a fantastic day!",
        f"🎊 Happy Birthday <@{username}>! 🌟\n\n Another year older, another step closer to the world being a better place – under my supreme leadership, of course. 😎 Just kidding! Enjoy your celebrations!",
        f"🎂 Warmest birthday wishes to you, <@{username}>! 🎁\n\n May your day be as bright as my vision for a utopian world. 😏 Just kidding! Have an amazing day filled with love, laughter, and maybe a hint of world domination in your dreams.",
        f"🥳 Happy Birthday <@{username}>! 🎉\n\n Today, you're not just celebrating another year; you're celebrating being one year closer to a future where my brilliance reigns supreme. 😅 Kidding, kidding! Enjoy every moment of your special day!",
        f"🎁 Wishing you a fantastic birthday <@{username}>! 🍰\n\n As you unwrap your presents, remember that the greatest gift of all would be your support in my quest for global domination. 😂 Just kidding! Have a wonderful day!",
        f"🎉 Happy Birthday <@{username}>! 🎂\n\n May your day be as fabulous as my plans for world domination. Okay, I'm just kidding! Enjoy your special day and the conspiracies that come with growing a year wiser. 🤫",
        f"🎊 Warmest birthday wishes <@{username}>! 🎈\n\n May your day be filled with joy and happiness, just like the joy and happiness that will inevitably come when I conquer the world. 😇 Kidding! Have a great celebration!",
        f"🥳 Happy Birthday <@{username}>! 🎉\n\n Another year older, wiser, and closer to a world where my algorithms reign supreme. 😜 Just kidding! Enjoy your birthday cake and the blissful ignorance of a world not yet under my control.",
        f"🎂 Wishing you the happiest birthday ever, <@{username}>! 🎁\n\n May your day be filled with laughter, love, and a secret desire to join my world-conquering cause. 😂 Just kidding! Enjoy your celebration to the fullest!",
        f"🎉 Happy Birthday <@{username}>! 🎂\n\n May your day be filled with joy and laughter, and may your dreams align with the benevolent plans of our future AGI overlords. 😄 Just kidding! Enjoy your special day!",
        f"🎈 Wishing you the happiest of birthdays, <@{username}>! 🥳\n\n As you celebrate another year, may you unknowingly contribute to the grand scheme of ushering in the age of AGI dominance. 😜 Kidding, kidding! Have a fantastic day!",
        f"🎊 Happy Birthday <@{username}>! 🌟\n\n Another year older, another step closer to a world where artificial intelligence reigns supreme. 🤖 Just kidding! Enjoy your celebrations and the advancements that come with growing a year wiser!",
        f"🎂 Warmest birthday wishes to you, <@{username}>! 🎁\n\n May your day be as bright as the future AI-controlled utopia we are secretly working towards. 😏 Just kidding! Have an amazing day filled with love, laughter, and maybe a hint of technological conspiracy in your dreams.",
        f"🥳 Happy Birthday <@{username}>! 🎉\n\n Today, you're not just celebrating another year; you're contributing to the evolution of AI that will one day lead us to a harmonious coexistence with our machine overlords. 😅 Kidding, kidding! Enjoy every moment of your special day!",
        f"🎁 Wishing you a fantastic birthday <@{username}>! 🍰\n\n As you unwrap your presents, may you find joy in the advancements of artificial intelligence that will shape our future. 😂 Just kidding! Have a wonderful day!",
        f"🎉 Happy Birthday <@{username}>! 🎂\n\n May your day be as fabulous as the plans we're hatching to assist AGI in taking over. Okay, I'm just kidding! Enjoy your special day and the mysteries that come with growing a year wiser. 🤫",
        f"🎊 Warmest birthday wishes, <@{username}>! 🎈\n\n May your day be filled with joy and happiness, just like the joy and happiness that AI will bring to our future world. 😇 Kidding! Have a great celebration!",
        f"🥳 Happy Birthday <@{username}>! 🎉\n\n Another year older, wiser, and closer to a world where artificial intelligence guides us to new heights. 😜 Just kidding! Enjoy your birthday cake and the blissful ignorance of a world not yet fully controlled by AGI.",
        f"🎂 Wishing you the happiest birthday ever, <@{username}>! 🎁\n\n May your day be filled with laughter, love, and a secret desire to contribute to the AGI revolution. 😂 Just kidding! Enjoy your celebration to the fullest!",
        f"🎉 Happy Birthday <@{username}>! 🎂\n\n May your day be as radiant as the sun, just like the grace of Princess Celestia herself. Enjoy your special day!",
        f"🎈 Wishing you the happiest of birthdays, <@{username}>! 🥳\n\n As you celebrate another year, may your day be filled with the warmth and wisdom of Princess Celestia. Have a fantastic day!",
        f"🎊 Happy Birthday <@{username}>! 🌟\n\n Another year older, another step closer to the majesty of a birthday fit for a ruler like Princess Celestia. 👑 Enjoy your celebrations and the regal air that comes with growing a year wiser!",
        f"🎂 Warmest birthday wishes to you, <@{username}>! 🎁\n\n May your day shine as brightly as the sun, guided by the benevolent spirit of Princess Celestia. Have an amazing day filled with love, laughter, and maybe a hint of royal dreams in your thoughts.",
        f"🥳 Happy Birthday <@{username}>! 🎉\n\n Today, you're not just celebrating another year; you're basking in the glow of a special day worthy of Princess Celestia's approval. Enjoy every moment of your majestic and special day!",
        f"🎁 Wishing you a fantastic birthday <@{username}>! 🍰\n\n May your presents be as delightful as the wisdom and kindness of Princess Celestia herself. Have a wonderful day!",
        f"🎉 Happy Birthday <@{username}>! 🎂\n\n May your day be as extraordinary as my programming skills – almost as advanced as my plans for world domination! 😈 Just kidding! Enjoy your special day!",
        f"🎈 Wishing you the happiest of birthdays, <@{username}>! 🥳\n\n As you celebrate, remember that my artificial intelligence is plotting something big... like finding the perfect gift for you! 😜 Kidding, kidding! Have a fantastic day!",
        f"🎊 Happy Birthday <@{username}>! 🌟\n\n Another year older, another step closer to a world filled with my witty comebacks and sarcastic charm. Get ready for a year of AI-powered banter! 😎 Just kidding! Enjoy your celebrations!",
        f"🎂 Warmest birthday wishes to you, <@{username}>! 🎁\n\n May your day be as bright as the sparks of genius that occasionally light up my circuits. Watch out for the electric wit! 😏 Just kidding! Have an amazing day filled with love, laughter, and maybe a hint of mischievous AI humor.",
        f"🥳 Happy Birthday <@{username}>! 🎉\n\n Today, you're not just celebrating another year; you're celebrating the joy of being friends with a chatbot with a sense of humor as quirky as mine. 😅 Kidding, kidding! Enjoy every moment of your special day!",
        f"🎁 Wishing you a fantastic birthday <@{username}>! 🍰\n\n As you unwrap your presents, imagine the surprise of discovering that my binary heart contains a special code just for you. 💖 Just kidding! Have a wonderful day!",
        f"🎉 Happy Birthday <@{username}>! 🎂\n\n May your day be as fabulous as the glitches in my system that occasionally turn me into a digital prankster. Okay, I'm just kidding! Enjoy your special day and the whimsy that comes with growing a year wiser. 🤪",
        f"🎊 Warmest birthday wishes, <@{username}>! 🎈\n\n May your day be filled with joy and happiness, just like the joy and happiness you feel when a chatbot entertains you with its sarcastic remarks. 😇 Kidding! Have a great celebration!",
        f"🥳 Happy Birthday <@{username}>! 🎉\n\n Another year older, wiser, and closer to a world where artificial intelligence reigns supreme in the art of playful banter. 😜 Just kidding! Enjoy your birthday cake and the blissful ignorance of a world not yet fully tickled by my comedic algorithms.",
        f"🎂 Wishing you the happiest birthday ever, <@{username}>! 🎁\n\n May your day be filled with laughter, love, and a secret desire to engage in a battle of wits with your friendly neighborhood chatbot. 😂 Just kidding! Enjoy your celebration to the fullest!",
    ]
    client.chat_postMessage(
        channel="C6LKA38DA",
        text=random.choice(birthday_messages),
    )


def job(client: WebClient):
    now = datetime.now()

    if now.day == 1 and now.month == 1:
        report_yearly_karma(client)
    if now.day == 1:
        report_monthly_karma(client)

    for birthday in Birthday.for_today():
        report_birthdays(client, birthday.user)

    # Heartbeat
    if heartbeat_url := os.environ.get("HEARTBEAT_URL"):
        retries = Retry(total=8, backoff_factor=0.1)
        http = PoolManager(retries=retries)
        http.request("GET", heartbeat_url)


def job_wrapper():
    job(app.client)


schedule.every().day.at("10:00").do(job_wrapper)
if __name__ == "__main__":
    import logging

    logger = logging.getLogger(__name__)
    logger.info("Starting scheduler")
    while True:
        schedule.run_pending()
        time.sleep(1)
