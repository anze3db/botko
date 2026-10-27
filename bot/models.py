from datetime import datetime, timedelta

from django.db import models


class SlackUser(models.Model):
    slack_id = models.CharField(max_length=20, unique=True, db_index=True)
    display_name = models.TextField(blank=True, default="")
    real_name = models.TextField(blank=True, default="")
    avatar_url = models.URLField(max_length=500, blank=True, default="")
    is_bot = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.display_name or self.slack_id} ({self.slack_id})"


class Channel(models.Model):
    slack_id = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.TextField(blank=True, default="")
    is_private = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.name or self.slack_id} ({self.slack_id})"


class Message(models.Model):
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name="messages"
    )
    user = models.ForeignKey(
        SlackUser, on_delete=models.CASCADE, related_name="messages"
    )
    ts = models.CharField(max_length=50, db_index=True)
    thread_ts = models.CharField(max_length=50, blank=True, default="")
    text = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=datetime.now)

    class Meta:
        unique_together = [("channel", "ts")]

    def __str__(self):
        return f"Message by {self.user} at {self.ts}"


class Attachment(models.Model):
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="attachments"
    )
    slack_file_id = models.CharField(max_length=50, blank=True, default="")
    original_url = models.URLField(max_length=1000, blank=True, default="")
    file = models.FileField(upload_to="attachments/%Y/%m/")
    filename = models.TextField(blank=True, default="")
    content_type = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment {self.filename} on {self.message}"


class Karma(models.Model):
    channel = models.TextField()
    ts = models.TextField()
    user = models.TextField()
    emoji = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.now)

    giver = models.ForeignKey(
        SlackUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="karma_given",
    )
    receiver = models.ForeignKey(
        SlackUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="karma_received",
    )
    channel_ref = models.ForeignKey(
        Channel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="karma_events",
    )
    message = models.ForeignKey(
        Message,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="karma_events",
    )

    def __str__(self):
        return f"{self.user} in {self.channel}"

    @classmethod
    def give_karma(
        cls,
        channel: str,
        ts: str,
        users: list[str],
        giver_slack_id: str | None = None,
        emoji: str | None = None,
    ):
        giver_obj = None
        if giver_slack_id:
            giver_obj, _ = SlackUser.objects.get_or_create(
                slack_id=giver_slack_id,
                defaults={"display_name": giver_slack_id},
            )

        channel_obj, _ = Channel.objects.get_or_create(
            slack_id=channel,
            defaults={"name": channel},
        )

        message_obj = Message.objects.filter(channel=channel_obj, ts=ts).first()

        karma_objects = []
        for user_id in users:
            receiver_obj, _ = SlackUser.objects.get_or_create(
                slack_id=user_id,
                defaults={"display_name": user_id},
            )
            karma_objects.append(
                cls(
                    channel=channel,
                    ts=ts,
                    user=user_id,
                    emoji=emoji,
                    giver=giver_obj,
                    receiver=receiver_obj,
                    channel_ref=channel_obj,
                    message=message_obj,
                )
            )
        cls.objects.bulk_create(karma_objects)

    @classmethod
    def leaderboard(cls):
        year = datetime.now().year
        return (
            cls.objects.filter(
                created_at__year=year,
            )
            .values("user")
            .annotate(count=models.Count("id"))
            .order_by("-count", "user")
        )

    @classmethod
    def leaderboard_prev_month(cls):
        prev_month = datetime.now().replace(day=1) - timedelta(days=1)
        return (
            cls.objects.filter(
                created_at__year=prev_month.year,
                created_at__month=prev_month.month,
            )
            .values("user")
            .annotate(count=models.Count("id"))
            .order_by("-count", "user")
        )

    @classmethod
    def leaderboard_prev_year(cls):
        prev_year = datetime.now().replace(day=1, month=1) - timedelta(days=1)
        return (
            cls.objects.filter(
                created_at__year=prev_year.year,
            )
            .values("user")
            .annotate(count=models.Count("id"))
            .order_by("-count", "user")
        )

    @classmethod
    def giver_leaderboard(cls):
        year = datetime.now().year
        return (
            cls.objects.filter(created_at__year=year, giver__isnull=False)
            .values("giver__slack_id", "giver__display_name", "giver__avatar_url")
            .annotate(count=models.Count("id"))
            .order_by("-count")
        )

    @classmethod
    def top_messages(cls, limit=20):
        year = datetime.now().year
        return (
            cls.objects.filter(created_at__year=year, message__isnull=False)
            .values("message__id")
            .annotate(karma_count=models.Count("id"))
            .order_by("-karma_count")[:limit]
        )


class Birthday(models.Model):
    user = models.TextField(unique=True)
    day = models.IntegerField()
    month = models.IntegerField()

    def __str__(self):
        return f"{self.user}: {self.day}/{self.month}"

    @classmethod
    def for_today(cls):
        now = datetime.now()
        return cls.objects.filter(day=now.day, month=now.month)
