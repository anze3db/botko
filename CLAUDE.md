# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Botko is a Slack bot (spiritual successor to [psywerx/botko](https://github.com/psywerx/botko)) that manages a karma system and birthday wishes for a Slack workspace. Users give karma via `++` mentions or emoji reactions, and the bot tracks leaderboards and sends scheduled reports.

## Commands

```bash
# Setup
cp .env.example .env
uv sync

# Run migrations
uv run python manage.py migrate

# Run tests (watch mode)
uv run ptw .

# Run tests once
uv run pytest

# Run dev server
uv run python manage.py runserver 3000

# Run the background worker (also runs the periodic schedule)
uv run python manage.py potatoq worker
```

Package manager is **uv** (not pip/pipenv). Python 3.15+.

## Architecture

Django + PostgreSQL. Two-process system:

1. **Web server** (`botko/wsgi.py`) - Django WSGI app handling Slack events via Slack Bolt's Django adapter. Receives messages/reactions at `/slack/events`, serves a heartbeat at `/`. Runs under Gunicorn in production.

2. **Worker** (`python manage.py potatoq worker`) - A [potatoq](https://anze3db.github.io/potatoq/) worker that uses the Django database as its broker and runs `POTATOQ["beat_schedule"]` from `botko/settings.py`. The `daily-report` task runs at 10:00 Europe/Lisbon (`POTATOQ["timezone"]`) and posts monthly/yearly karma reports and birthday wishes to a hardcoded Slack channel (`C6LKA38DA`). Deployed as the `botko-scheduler` systemd service.

Single Django app: `bot/`
- `bot/models.py` - Django ORM models (`Karma`, `Birthday`) with classmethod query helpers
- `bot/slack_app.py` - Slack Bolt `App` instance and all message/event handlers
- `bot/slack_urls.py` - Wires Slack Bolt into Django URL routing
- `bot/tasks.py` - potatoq tasks (`daily_report`) and the report/birthday jobs they run
- `bot/utils.py` - `KARMA_EMOJIS` tuple and `parse_karma_from_text()` regex parser

## Key Patterns

- Database access uses Django ORM (models in `bot/models.py`)
- Tests run against Postgres (`DATABASE_URL`, a `postgres:18` service in CI) and use `freezegun` for time-dependent logic
- Tests use `@pytest.mark.django_db` decorator for database access
- Slack API calls are mocked with `autospec=True` in tests
- Karma cannot be self-assigned (enforced in `bot/slack_app.py`)
- `TIME_ZONE = "UTC"` is set explicitly: with `USE_TZ = False` Django exports it as the process TZ, so it controls `datetime.now()` and stored `created_at` values (unset, it defaults to America/Chicago). Crontabs fire in `POTATOQ["timezone"]` (Europe/Lisbon) instead
- Tests that enqueue and `drain()` potatoq tasks need `@pytest.mark.django_db(transaction=True)`: the broker reads the queue on its own connection
- Sentry integration is conditional on `SENTRY_DNS` env var being set
