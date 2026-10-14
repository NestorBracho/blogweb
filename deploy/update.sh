#!/usr/bin/env bash
# Pull the latest code and reload the app. Run on the server as the "blog" user.
set -euo pipefail

cd /srv/blog/app
gunicorn_before=$(/srv/blog/venv/bin/gunicorn --version)
git pull --ff-only
/srv/blog/venv/bin/pip install -q -r requirements.txt
/srv/blog/venv/bin/python manage.py migrate --noinput
/srv/blog/venv/bin/python manage.py collectstatic --noinput -v0
if [ "$(/srv/blog/venv/bin/gunicorn --version)" = "$gunicorn_before" ]; then
    # Graceful reload: the socket stays open, so requests wait for the new workers instead of failing.
    # Starts the service instead if it isn't running.
    sudo systemctl reload-or-restart blog
else
    # The master process keeps running the Gunicorn it started with: only a restart picks up the new one
    sudo systemctl restart blog
fi
echo "Deployed $(git rev-parse --short HEAD)"
