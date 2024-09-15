#!/bin/bash
set -e
pushd "$(dirname "$0")/.."
git pull
uv sync --frozen
sudo kill -hup `cat gunicorn.pid`
sudo systemctl restart botko-scheduler
echo `date "+%Y-%m-%d %H:%M:%S.%3N"` ' Updated' >> update.log
popd
