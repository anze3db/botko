#!/bin/bash
set -e
pushd "$(dirname "$0")/.."
uv run --locked python scheduler.py
popd
