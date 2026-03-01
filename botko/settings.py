from pathlib import Path

import environ

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
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
    },
]

ROOT_URLCONF = "botko.urls"

WSGI_APPLICATION = "botko.wsgi.application"

DATABASES = {
    "default": env.db(),
}

USE_TZ = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if sentry_dns := env("SENTRY_DNS", default=""):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        sentry_dns,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
    )
