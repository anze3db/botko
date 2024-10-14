# Botko 🤖

[![Upgrade dependencies](https://github.com/anze3db/botko/actions/workflows/upgrade-dependencies.yml/badge.svg?branch=main&event=schedule)](https://github.com/anze3db/botko/actions/workflows/upgrade-dependencies.yml)
[![Test & Deploy](https://github.com/anze3db/botko/actions/workflows/test-deploy.yml/badge.svg)](https://github.com/anze3db/botko/actions/workflows/python.yml)
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

Run server:
```
uv run uvicorn app:api --log-level info --reload --port 3000
```

You'll need to set the `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` `env` variables from https://api.slack.com/apps/


If you want Slack to be able to hit your server you'll also need to run `ngrok`:
```
ngrok http 3000
```
