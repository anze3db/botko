# Botko 🤖

A spiritual successor to https://github.com/psywerx/botko


## Development

Create an `.env` file:
```
cp .env.example .env
```

Set up the dev environment:

```
python -m venv .venv  # Should be using Python 3.10 or newer
. .venv/bin/activate
pip install pip-tools
pip-sync requirements.txt dev-requirements.txt
```

Run tests:
```
ptw
```

Run server:
```
uvicorn app:api --log-level info --reload --port 3000
```

You'll need to set the `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` `env` variables from https://api.slack.com/apps/


If you want Slack to be able to hit your server you'll also need to run `ngrok`:
```
ngrok http 3000
```
