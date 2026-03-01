from django.urls import path
from slack_bolt.adapter.django import SlackRequestHandler

from bot.slack_app import app

handler = SlackRequestHandler(app=app)


def events(request):
    return handler.handle(request)


urlpatterns = [
    path("events", events, name="slack_events"),
]
