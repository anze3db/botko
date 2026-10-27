# Botko 🤖

[![Test & Deploy](https://github.com/anze3db/botko/actions/workflows/python.yml/badge.svg)](https://github.com/anze3db/botko/actions/workflows/python.yml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

A spiritual successor to https://github.com/psywerx/botko


## Development

Create an `.env` file:
```
cp .env.example .env
```

Set up the dev environment:

```
uv sync
```

Run tests:
```
uv run ptw
```

Run migrations:
```
uv run python manage.py migrate
```

Run server:
```
uv run python manage.py runserver
```

You'll need to set the `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` `env` variables from https://api.slack.com/apps/
The bot token needs the `files:read` scope to save the files people share.

The karma chart at `/` is public. The leaderboards and top posts need an account:
```
uv run python manage.py createsuperuser
```


If you want Slack to be able to hit your server you'll also need to run `ngrok`:
```
ngrok http 8000
```
