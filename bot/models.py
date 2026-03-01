from datetime import datetime, timedelta

from django.db import models


class Karma(models.Model):
    channel = models.TextField()
    ts = models.TextField()
    user = models.TextField()
    emoji = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.now)

    class Meta:
        db_table = "karma"

    def __str__(self):
        return f"{self.user} in {self.channel}"

    @classmethod
    def give_karma(cls, channel: str, ts: str, users: list[str]):
        cls.objects.bulk_create(
            [cls(channel=channel, ts=ts, user=user) for user in users]
        )

    @classmethod
    def leaderboard(cls):
        year = datetime.now().year
        return (
            cls.objects.filter(
                created_at__year=year,
            )
            .values("user")
            .annotate(count=models.Count("id"))
            .order_by("-count")
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
            .order_by("-count")
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
            .order_by("-count")
        )


class Birthday(models.Model):
    user = models.TextField(unique=True)
    day = models.IntegerField()
    month = models.IntegerField()

    class Meta:
        db_table = "birthday"

    def __str__(self):
        return f"{self.user}: {self.day}/{self.month}"

    @classmethod
    def for_today(cls):
        now = datetime.now()
        return cls.objects.filter(day=now.day, month=now.month)
