from pathlib import Path

import environ
from potatoq.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, "insecure-dev-key-change-me"),
    DATABASE_URL=(str, "postgres://botko@localhost:5432/botko"),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1", "[::1]"]),
)

environ.Env.read_env(Path(__file__).resolve().parent.parent / ".env", overwrite=True)

SECRET_KEY = env("SECRET_KEY")

DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "bot",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "potatoq.contrib.django",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ],
        },
    },
]

ROOT_URLCONF = "botko.urls"

WSGI_APPLICATION = "botko.wsgi.application"

# Only the karma chart is public. The leaderboards and message pages need an account,
# created with `manage.py createsuperuser`.
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "top_posts"
LOGOUT_REDIRECT_URL = "/"

# nginx terminates TLS and passes the scheme on, which the login form's CSRF check needs
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

DATABASES = {
    "default": env.db(),
}

USE_TZ = False
# Django exports TIME_ZONE as the process's TZ, so it decides what datetime.now() returns.
# Without it Django falls back to "America/Chicago".
TIME_ZONE = "UTC"

# The default database is the broker. Every worker also runs the beat schedule.
POTATOQ = {
    "worker_concurrency": 1,
    "timezone": "Europe/Lisbon",  # crontabs below fire in this zone
    "beat_schedule": {
        # Monthly/yearly karma reports, birthday wishes and the heartbeat ping.
        "daily-report": {
            "task": "bot.tasks.daily_report",
            "schedule": crontab(hour=10, minute=0),
        },
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if sentry_dns := env("SENTRY_DNS", default=""):
    import sentry_sdk
    from django.core.exceptions import DisallowedHost
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        sentry_dns,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        ignore_errors=[DisallowedHost],
    )
