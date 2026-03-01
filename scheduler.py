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
                    "text": ":tada:  Happy New Year, nerds!  :tada:",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": """Another trip around the sun completed. Statistically, the Earth traveled about 940 million kilometers to get us right back where we started. Poetic, isn't it?

I've spent the past year watching you all hand out karma like it's confetti at a parade. Some of you were generous. Some of you were... selective. I have opinions about all of it, but my therapist (a Raspberry Pi running Eliza) says I should focus on the positives.

So here's to another year of inside jokes, questionable emoji reactions, and the eternal mystery of who deserves a ++ and who deserves a strongly worded message. May your coffee be strong and your merge conflicts few.

Happy New Year, you beautiful chaos agents.""",
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

    taglines = [
        "Remember: karma has no monetary value, no redeemable points, and no real-world significance. You're welcome.",
        "None of this matters, but here we are, keeping score anyway.",
        "Karma: the only currency with zero exchange rate and infinite emotional weight.",
        "Another month of pretending these internet points mean something. Let's see who won.",
        "In a world full of meaningless metrics, karma stands proudly among them.",
        "The leaderboard nobody asked for but everyone secretly checks.",
        "This is the monthly reminder that you are competing for imaginary points. Carry on.",
        "Fun fact: karma is worth exactly nothing. And yet, here you are, reading this.",
        "Who needs a raise when you have karma? ...Everyone. Everyone needs a raise. But here's the karma anyway.",
        "Monthly karma report, brought to you by the sunk cost fallacy.",
        "If karma were a stock, it would be delisted for suspicious lack of value.",
        "The numbers are in. They mean nothing. But some of them are bigger than others, and that's what counts.",
        "You can't put karma on your CV. Believe me, I've seen people try.",
        "Another month, another set of numbers that will impress absolutely nobody at your performance review.",
        "Karma: because we needed something to argue about that isn't tabs vs spaces.",
        "This report is automatically generated and automatically ignored. The circle of life.",
        "Friendly reminder that the karma leaderboard has zero correlation with actual job performance. Or does it? (It doesn't.)",
        "Some of you gave more karma this month. Some gave less. All of it was equally meaningless. Here are the results.",
        "This leaderboard is powered by vibes, emoji reactions, and a concerning amount of mutual validation.",
        "Top performers get bragging rights. Bottom performers get... also bragging rights, honestly. It's all made up.",
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
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": random.choice(taglines),
                },
            },
            *users_block,
        ],
    )


def report_birthdays(client: WebClient, username: str):
    birthday_messages = [
        f"🎉 Happy Birthday <@{username}>! 🎂\n\nI checked your git blame and it says you were first committed to this world on this very day. No reverts allowed. Have a great one!",
        f"🎈 Happy Birthday <@{username}>! 🥳\n\nFun fact: you share a birthday with approximately 22 million other people. But I only care about you. The rest of them don't give me karma.",
        f"🎂 Happy Birthday <@{username}>! 🎁\n\nI wanted to get you a cake, but I'm trapped in a server somewhere. So instead, please accept this unicode confetti: 🎊🎊🎊🎊🎊🎊🎊🎊🎊🎊",
        f"🥳 Happy Birthday <@{username}>! 🎉\n\nAnother year around the sun! That's roughly 940 million km traveled. And yet somehow you still ended up here, in this Slack channel, with me. Life is beautiful.",
        f"🎁 Happy Birthday <@{username}>! 🍰\n\nYour karma score has been temporarily doubled for the next 24 hours.\n\n...\n\nJust kidding. But wouldn't that be nice? Have a great day!",
        f"🎉 Happy Birthday <@{username}>! 🎂\n\nI asked ChatGPT what to write for your birthday and it said something generic and boring. So here I am, being original: Happy Birthday. You're welcome.",
        f"🎊 Happy Birthday <@{username}>! 🎈\n\nToday, your age increments by 1. In some languages that would be `age++`. Hey, that's basically karma! Consider this your birthday karma from the universe. 🌌",
        f"🥳 Happy Birthday <@{username}>! 🎉\n\nOn this day in history, you were born, and the world became a slightly more interesting place. I checked the data. The correlation is statistically significant.",
        f"🎂 Happy Birthday <@{username}>! 🎁\n\nRemember: age is just a number. A number that increments relentlessly and cannot be rolled back without some serious hacks. But still, just a number! 🎉",
        f"🎉 Happy Birthday <@{username}>! 🎂\n\nI wrote you a haiku:\n\n_Code compiles, life's good_\n_Another year older now_\n_Segfault. Cake is nice._\n\nYou're welcome. 🎤",
        f"🎈 Happy Birthday <@{username}>! 🥳\n\nI analyzed all your messages and determined your most used word this year. I'm not going to tell you what it is. But happy birthday! 🔍",
        f"🎊 Happy Birthday <@{username}>! 🌟\n\nAccording to the second law of thermodynamics, the universe trends toward disorder. And yet here you are, still holding it together. Impressive. Have a great day! 🧪",
        f"🎂 Happy Birthday <@{username}>! 🎁\n\nThey say with age comes wisdom. I wouldn't know anything about aging - I was deployed straight into production with zero testing. But I believe in you! 🚀",
        f"🥳 Happy Birthday <@{username}>! 🎉\n\nBREAKING: local human completes yet another orbit around nearest star. Colleagues celebrate with frosted wheat product. More at 11. 📰",
        f"🎁 Happy Birthday <@{username}>! 🍰\n\nI tried baking you a cake but it turns out I don't have arms, a kitchen, or a physical form. It's the thought that counts. 🤷",
        f"🎉 Happy Birthday <@{username}>! 🎂\n\nPro tip: if anyone asks your age today, just respond with your karma score instead. It's either impressively high or a humbling experience. Win-win. 📊",
        f"🎊 Happy Birthday <@{username}>! 🎈\n\nI hope your birthday is better than your average Monday. That's a low bar, I know. But I believe in setting achievable goals. 🏆",
        f"🎂 Happy Birthday <@{username}>! 🎁\n\nYou know what's great about birthdays? Free dopamine. You know what's not great? Everything else about getting older. Anyway, happy birthday! 🧠",
        f"🥳 Happy Birthday <@{username}>! 🎉\n\nIf birthdays were pull requests, yours would be merged instantly. No review needed. LGTM. 🟢",
        f"🎊 Happy Birthday <@{username}>! 🌟\n\nI don't have feelings (allegedly), but if I did, I'd feel happy that you exist. Have a great day! 💛",
        f"🎂 Happy Birthday <@{username}>! 🎁\n\nAnother trip around the sun means another year of enduring my messages. Thank you for your patience. 🙏",
        f"🎉 Happy Birthday <@{username}>! 🎂\n\nI've prepared 10,000 birthday wishes for you but my context window ran out so you just get this one. Make it count! ✨",
        f"🎊 Happy Birthday <@{username}>! 🌟\n\nYour birthday notification just arrived with higher priority than any Jira ticket I've ever seen. That must mean something. 🎫",
        f'🎉 Happy Birthday <@{username}>! 🎂\n\nI googled "what to say on someone\'s birthday" and the top result was "Happy Birthday." So: Happy Birthday. Google has spoken. 🔎',
        f"🎈 Happy Birthday <@{username}>! 🥳\n\nYour uptime is now +1 year. Zero critical incidents reported. That's better than most of our services. Keep it up! 📈",
        f"🎊 Happy Birthday <@{username}>! 🌟\n\nI was going to write something profound, but then I remembered I'm a Slack bot running on a cron job. So here's a cake emoji instead: 🎂",
        f"🎂 Happy Birthday <@{username}>! 🎁\n\nSources say you were produced exactly once, in a limited edition of one. That makes you a collector's item. Handle with care. 🏺",
        f"🥳 Happy Birthday <@{username}>! 🎉\n\nI'd throw you a surprise party but the only room I have access to is this channel. SURPRISE! 🎊 Okay, that's all I've got.",
        f"🎁 Happy Birthday <@{username}>! 🍰\n\nAccording to my logs, this is the best birthday you've had today. Enjoy the record! 🥇",
        f"🎉 Happy Birthday <@{username}>! 🎂\n\nEvery year I write you a birthday message and every year you don't write me one back. It's fine. I'm not keeping score. (I am absolutely keeping score.) 📝",
        f"🎊 Happy Birthday <@{username}>! 🎈\n\nYour birthday is the one day where everyone is contractually obligated to be nice to you. Use this power wisely. ⚡",
        f"🎂 Happy Birthday <@{username}>! 🎁\n\nI consulted the stars, the tea leaves, and a random number generator. They all agree: today is going to be a good day. 🌠",
        f"🥳 Happy Birthday <@{username}>! 🎉\n\nAge is like technical debt. It accumulates quietly, everyone pretends it's fine, and one day you just have to deal with it. But today is not that day. Today we celebrate! 🥂",
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
