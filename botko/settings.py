import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "insecure-dev-key-change-me")

DEBUG = os.environ.get("DEBUG", "") == "True"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "bot",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "botko.urls"

WSGI_APPLICATION = "botko.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME", "botko"),
        "USER": os.environ.get("DATABASE_USER", "botko"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""),
        "HOST": os.environ.get("DATABASE_HOST", "localhost"),
        "PORT": os.environ.get("DATABASE_PORT", "5432"),
    }
}

USE_TZ = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if sentry_dns := os.environ.get("SENTRY_DNS"):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        sentry_dns,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
    )
