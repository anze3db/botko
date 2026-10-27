from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path

from bot.views import attachment, index, top_givers, top_posts, top_receivers

urlpatterns = [
    path("", index),
    path("login/", LoginView.as_view(template_name="bot/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("receivers/", top_receivers, name="top_receivers"),
    path("givers/", top_givers, name="top_givers"),
    path("posts/", top_posts, name="top_posts"),
    path("attachments/<int:attachment_id>/", attachment, name="attachment"),
    path("slack/", include("bot.slack_urls")),
]
