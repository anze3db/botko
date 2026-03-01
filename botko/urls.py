from django.urls import include, path

from bot.views import index

urlpatterns = [
    path("", index),
    path("slack/", include("bot.slack_urls")),
]
