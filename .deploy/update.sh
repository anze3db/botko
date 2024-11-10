#!/bin/bash
set -e
pushd "$(dirname "$0")/.."
git pull
uv sync --locked
sudo systemctl reload botko
sudo systemctl restart botko-scheduler
echo `date "+%Y-%m-%d %H:%M:%S.%3N"` ' Updated' >> update.log
popd
