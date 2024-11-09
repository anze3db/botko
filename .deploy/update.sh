#!/bin/bash
set -e
pushd "$(dirname "$0")/.."
git pull
uv sync --locked
ps axf | grep 'gunicorn: master \[botko\]' | awk '{print "sudo kill -hup " $1}' | sh
sudo systemctl restart botko-scheduler
echo `date "+%Y-%m-%d %H:%M:%S.%3N"` ' Updated' >> update.log
popd
