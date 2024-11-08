#!/bin/bash
set -e
pushd "$(dirname "$0")/.."
git pull
uv sync --locked
sudo kill -hup `cat /var/run/gunicorn-botko.pidd`
sudo systemctl restart botko-scheduler
echo `date "+%Y-%m-%d %H:%M:%S.%3N"` ' Updated' >> update.log
popd
