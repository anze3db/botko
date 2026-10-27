from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from bot.views import index, top_givers, top_posts, top_receivers

urlpatterns = [
    path("", index),
    path("receivers/", top_receivers, name="top_receivers"),
    path("givers/", top_givers, name="top_givers"),
    path("posts/", top_posts, name="top_posts"),
    path("slack/", include("bot.slack_urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
