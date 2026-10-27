import pytest
from django.core.files.base import ContentFile
from django.test import Client

from bot.models import Attachment, Channel, Karma, Message, SlackUser

PRIVATE_PAGES = ["/receivers/", "/givers/", "/posts/"]


def make_attachment(filename, content_type, data=b"data"):
    user = SlackUser.objects.create(slack_id="UAUTHOR", display_name="Author")
    channel = Channel.objects.create(slack_id="C1", name="general")
    msg = Message.objects.create(channel=channel, user=user, ts="1.0", text="look")
    Karma.objects.create(channel="C1", ts="1.0", user="UAUTHOR", message=msg)
    att = Attachment(message=msg, filename=filename, content_type=content_type)
    att.file.save(filename, ContentFile(data))
    return att


@pytest.mark.django_db
def test_index_view(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'href="/login/"' in response.content
    assert b'href="/posts/"' not in response.content


@pytest.mark.django_db
def test_index_view_with_data(client):
    Karma.give_karma("C1", "t1", ["U123"])
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_index_view_logged_in(admin_client):
    response = admin_client.get("/")
    assert b'href="/posts/"' in response.content
    assert b"Log out" in response.content


@pytest.mark.django_db
@pytest.mark.parametrize("url", PRIVATE_PAGES)
def test_private_pages_need_login(client, url):
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == f"/login/?next={url}"


@pytest.mark.django_db
def test_login_page(client):
    response = client.get("/login/?next=/givers/")
    assert response.status_code == 200
    assert b'value="/givers/"' in response.content


@pytest.mark.django_db
def test_login(client, admin_user):
    response = client.post(
        "/login/", {"username": "admin", "password": "password", "next": "/givers/"}
    )
    assert response.status_code == 302
    assert response.url == "/givers/"
    assert client.get("/givers/").status_code == 200


@pytest.mark.django_db
def test_login_wrong_password(client, admin_user):
    response = client.post("/login/", {"username": "admin", "password": "wrong"})
    assert response.status_code == 200
    assert b"Wrong username or password." in response.content


@pytest.mark.django_db
def test_logout(admin_client):
    response = admin_client.post("/logout/")
    assert response.status_code == 302
    assert admin_client.get("/posts/").status_code == 302


@pytest.mark.django_db
def test_slack_events_skip_csrf():
    # A 403 would mean the CSRF check rejected Slack before Bolt checked the signature
    response = Client(enforce_csrf_checks=True).post(
        "/slack/events", data="{}", content_type="application/json"
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_top_receivers_view(admin_client):
    SlackUser.objects.create(slack_id="U123", display_name="Receiver")
    Karma.give_karma("C1", "t1", ["U123"])
    response = admin_client.get("/receivers/")
    assert response.status_code == 200
    assert b"Receiver" in response.content


@pytest.mark.django_db
def test_top_receivers_empty(admin_client):
    response = admin_client.get("/receivers/")
    assert response.status_code == 200
    assert b"No karma received yet this year." in response.content


@pytest.mark.django_db
def test_top_givers_view(admin_client):
    SlackUser.objects.create(slack_id="UGIVER", display_name="Giver")
    Karma.give_karma("C1", "t1", ["U123"], giver_slack_id="UGIVER")
    response = admin_client.get("/givers/")
    assert response.status_code == 200
    assert b"Giver" in response.content


@pytest.mark.django_db
def test_top_givers_empty(admin_client):
    response = admin_client.get("/givers/")
    assert response.status_code == 200
    assert b"No karma given yet this year." in response.content


@pytest.mark.django_db
def test_top_posts_view(admin_client):
    user = SlackUser.objects.create(slack_id="UAUTHOR", display_name="Author")
    channel = Channel.objects.create(slack_id="C1", name="general")
    msg = Message.objects.create(channel=channel, user=user, ts="1.0", text="cool post")
    Karma.objects.create(
        channel="C1", ts="1.0", user="UAUTHOR", message=msg, emoji="fire"
    )
    response = admin_client.get("/posts/")
    assert response.status_code == 200
    assert b"cool post" in response.content
    assert b":fire: &times;1" in response.content


@pytest.mark.django_db
def test_top_posts_empty(admin_client):
    response = admin_client.get("/posts/")
    assert response.status_code == 200
    assert b"No posts with karma yet this year." in response.content


@pytest.mark.django_db
def test_top_posts_shows_attachments(admin_client):
    image = make_attachment("cat.png", "image/png")
    doc = Attachment(
        message=image.message, filename="notes.pdf", content_type="application/pdf"
    )
    doc.file.save("notes.pdf", ContentFile(b"%PDF"))
    response = admin_client.get("/posts/")
    assert f'<img class="post-image" src="/attachments/{image.id}/"'.encode() in (
        response.content
    )
    assert f'href="/attachments/{doc.id}/">notes.pdf</a>'.encode() in response.content


@pytest.mark.django_db
def test_attachment_image(admin_client):
    att = make_attachment("cat.png", "image/png", b"png bytes")
    response = admin_client.get(f"/attachments/{att.id}/")
    assert response.status_code == 200
    assert response["Content-Type"] == "image/png"
    assert response["Content-Disposition"] == 'inline; filename="cat.png"'
    assert response["X-Content-Type-Options"] == "nosniff"
    assert b"".join(response.streaming_content) == b"png bytes"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("filename", "content_type"),
    [("page.html", "text/html"), ("logo.svg", "image/svg+xml")],
)
def test_attachment_other_types_download(admin_client, filename, content_type):
    att = make_attachment(filename, content_type)
    response = admin_client.get(f"/attachments/{att.id}/")
    assert response.status_code == 200
    assert response["Content-Disposition"] == f'attachment; filename="{filename}"'


@pytest.mark.django_db
def test_attachment_needs_login(client):
    att = make_attachment("cat.png", "image/png")
    response = client.get(f"/attachments/{att.id}/")
    assert response.status_code == 302
    assert response.url == f"/login/?next=/attachments/{att.id}/"


@pytest.mark.django_db
def test_attachment_missing_file(admin_client):
    att = make_attachment("cat.png", "image/png")
    att.file.delete(save=False)
    response = admin_client.get(f"/attachments/{att.id}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_attachment_not_found(admin_client):
    response = admin_client.get("/attachments/1/")
    assert response.status_code == 404
