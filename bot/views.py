import json
from datetime import datetime

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import render

from bot.models import Karma, Message, SlackUser


def index(request):
    monthly_karma = (
        Karma.objects.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    labels = []
    counts = []
    cumulative = []
    running_total = 0

    for entry in monthly_karma:
        labels.append(entry["month"].strftime("%b %Y"))
        counts.append(entry["count"])
        running_total += entry["count"]
        cumulative.append(running_total)

    return render(
        request,
        "bot/index.html",
        {
            "labels_json": json.dumps(labels),
            "counts_json": json.dumps(counts),
            "cumulative_json": json.dumps(cumulative),
            "total_karma": running_total,
        },
    )


def top_receivers(request):
    year = datetime.now().year
    users_qs = (
        Karma.objects.filter(created_at__year=year)
        .values("user")
        .annotate(count=Count("id"))
        .order_by("-count")[:50]
    )

    users = []
    for entry in users_qs:
        slack_user = SlackUser.objects.filter(slack_id=entry["user"]).first()
        users.append(
            {
                "slack_id": entry["user"],
                "display_name": slack_user.display_name
                if slack_user
                else entry["user"],
                "avatar_url": slack_user.avatar_url if slack_user else "",
                "count": entry["count"],
            }
        )

    return render(
        request,
        "bot/top_receivers.html",
        {"users": users, "year": year},
    )


def top_givers(request):
    year = datetime.now().year
    users_qs = (
        Karma.objects.filter(created_at__year=year, giver__isnull=False)
        .values("giver__slack_id", "giver__display_name", "giver__avatar_url")
        .annotate(count=Count("id"))
        .order_by("-count")[:50]
    )

    users = [
        {
            "slack_id": entry["giver__slack_id"],
            "display_name": entry["giver__display_name"],
            "avatar_url": entry["giver__avatar_url"],
            "count": entry["count"],
        }
        for entry in users_qs
    ]

    return render(
        request,
        "bot/top_givers.html",
        {"users": users, "year": year},
    )


def top_posts(request):
    year = datetime.now().year
    posts_qs = (
        Karma.objects.filter(created_at__year=year, message__isnull=False)
        .values("message__id")
        .annotate(karma_count=Count("id"))
        .order_by("-karma_count")[:30]
    )

    posts = []
    for entry in posts_qs:
        message = (
            Message.objects.select_related("user", "channel")
            .prefetch_related("attachments")
            .get(id=entry["message__id"])
        )
        emojis = (
            Karma.objects.filter(message=message)
            .values("emoji")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        posts.append(
            {
                "message": message,
                "karma_count": entry["karma_count"],
                "emojis": list(emojis),
                "attachments": list(message.attachments.all()),
            }
        )

    return render(
        request,
        "bot/top_posts.html",
        {"posts": posts, "year": year},
    )
