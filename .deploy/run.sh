#!/bin/bash
set -e
pushd "$(dirname "$0")/.."
uv run --locked app:api --log-level=info
popd
