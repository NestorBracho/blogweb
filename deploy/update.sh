#!/usr/bin/env bash
# Pull the latest code and restart the app. Run on the server as the "blog" user.
set -euo pipefail

cd /srv/blog/app
git pull --ff-only
/srv/blog/venv/bin/pip install -q -r requirements.txt
/srv/blog/venv/bin/python manage.py migrate --noinput
/srv/blog/venv/bin/python manage.py collectstatic --noinput -v0
sudo systemctl restart blog
echo "Deployed $(git rev-parse --short HEAD)"
