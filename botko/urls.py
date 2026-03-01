from django.http import HttpResponse
from django.urls import include, path


def heartbeat(request):
    return HttpResponse("Hello 🤖")


urlpatterns = [
    path("", heartbeat),
    path("slack/", include("bot.slack_urls")),
]
