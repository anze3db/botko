# botko's development tasks: `just` lists them. Everything runs through uv.

set shell := ["bash", "-euo", "pipefail", "-c"]
set positional-arguments

# List the recipes
[private]
default:
    @just --list --unsorted

# Install Python and the dev dependencies
sync:
    uv sync

# Run the tests (needs Postgres at DATABASE_URL); arguments go to pytest (`just test bot/tests/test_slack_app.py -x`)
[group("test")]
test *args:
    uv run pytest "$@"

# Rerun the tests on every change
[group("test")]
test-watch:
    uv run ptw .

# Lint, format check and type check
[group("check")]
lint:
    uv run ruff check
    uv run ruff format --check
    uv run mypy .

# Format the code and apply ruff's safe fixes
[group("check")]
fmt:
    uv run ruff format
    uv run ruff check --fix

# Everything before a push: lint, then the tests
[group("check")]
check: lint test

# Apply the database migrations
[group("run")]
migrate:
    uv run python manage.py migrate

# Run the dev server at http://localhost:3000
[group("run")]
server:
    uv run python manage.py runserver 3000

# Run the background worker and the periodic schedule
[group("run")]
worker:
    uv run python manage.py potatoq worker

# Remove cache output
clean:
    rm -rf .pytest_cache .ruff_cache .mypy_cache
