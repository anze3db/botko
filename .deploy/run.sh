#!/bin/bash
set -e
pushd "$(dirname "$0")/.."
uv run --frozen app:api --log-level=info
popd
