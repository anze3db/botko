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

# Run scheduler
uv run python scheduler.py
```

Package manager is **uv** (not pip/pipenv). Python 3.14+.

## Architecture

Django + PostgreSQL. Two-process system:

1. **Web server** (`botko/wsgi.py`) - Django WSGI app handling Slack events via Slack Bolt's Django adapter. Receives messages/reactions at `/slack/events`, serves a heartbeat at `/`. Runs under Gunicorn in production.

2. **Scheduler** (`scheduler.py`) - Standalone process using the `schedule` library. Calls `django.setup()` at startup. Runs a daily job at 10:00 that posts monthly/yearly karma reports and birthday wishes to a hardcoded Slack channel (`C6LKA38DA`).

Single Django app: `bot/`
- `bot/models.py` - Django ORM models (`Karma`, `Birthday`) with classmethod query helpers
- `bot/slack_app.py` - Slack Bolt `App` instance and all message/event handlers
- `bot/slack_urls.py` - Wires Slack Bolt into Django URL routing
- `bot/utils.py` - `KARMA_EMOJIS` tuple and `parse_karma_from_text()` regex parser

## Key Patterns

- Database access uses Django ORM (models in `bot/models.py`)
- Tests use in-memory SQLite (`TESTING=true` env var) and `freezegun` for time-dependent logic
- Tests use `@pytest.mark.django_db` decorator for database access
- Slack API calls are mocked with `autospec=True` in tests
- Karma cannot be self-assigned (enforced in `bot/slack_app.py`)
- Sentry integration is conditional on `SENTRY_DNS` env var being set
