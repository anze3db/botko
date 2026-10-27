import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render

from bot.models import Attachment, Karma


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


@login_required
def top_receivers(request):
    return render(
        request,
        "bot/top_receivers.html",
        {"users": Karma.receiver_leaderboard(), "year": datetime.now().year},
    )


@login_required
def top_givers(request):
    return render(
        request,
        "bot/top_givers.html",
        {"users": Karma.giver_leaderboard(), "year": datetime.now().year},
    )


@login_required
def top_posts(request):
    return render(
        request,
        "bot/top_posts.html",
        {"posts": Karma.top_messages(), "year": datetime.now().year},
    )


@login_required
def attachment(request, attachment_id):
    att = get_object_or_404(Attachment, id=attachment_id)
    try:
        file = att.file.open("rb")
    except FileNotFoundError:
        raise Http404("Attachment file is missing") from None
    return FileResponse(
        file,
        as_attachment=not att.is_image,
        filename=att.filename,
        content_type=att.content_type if att.is_image else None,
    )
