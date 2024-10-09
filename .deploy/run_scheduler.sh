#!/bin/bash
set -e
pushd "$(dirname "$0")/.."
uv run --frozen python scheduler.py
popd
