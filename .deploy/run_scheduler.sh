#!/bin/bash
set -e
pushd "$(dirname "$0")/.."
uv run python scheduler.py
popd
