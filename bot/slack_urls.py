from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from slack_bolt.adapter.django import SlackRequestHandler

from bot.slack_app import app

handler = SlackRequestHandler(app=app)


@csrf_exempt  # Slack signs its requests instead, and Bolt verifies the signature
def events(request):
    return handler.handle(request)


urlpatterns = [
    path("events", events, name="slack_events"),
]
