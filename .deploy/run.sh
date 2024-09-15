#!/bin/bash
set -e
pushd "$(dirname "$0")/.."
uv run gunicorn app:api --log-level=info
popd
