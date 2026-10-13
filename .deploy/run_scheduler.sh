#!/bin/bash
set -e
pushd "$(dirname "$0")/.."
uv run --locked python manage.py potatoq worker
popd
