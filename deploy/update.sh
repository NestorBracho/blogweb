#!/usr/bin/env bash
# Pull the latest code and reload the app. Run on the server as the "blog" user.
#
# A deploy runs the copy of this script it started with: a change to it takes effect from the next deploy.
set -euo pipefail

VENV=/srv/blog/venv
DB=/srv/blog/data/db.sqlite3
BACKUPS=/srv/blog/backups
# Copies of the database taken before migrating
KEEP_COPIES=5

cd /srv/blog/app
gunicorn_before=$("$VENV/bin/gunicorn" --version)
git pull --ff-only
"$VENV/bin/pip" install -q -r requirements.txt

# Copy the database before migrations change it, so a migration that goes wrong can be undone (deploy/README.md).
# -readonly: if the database isn't there, fail instead of copying a new empty one.
if ! "$VENV/bin/python" manage.py migrate --check >/dev/null; then
    copy=$BACKUPS/pre-migrate-$(date +%F-%H%M%S)-$(git rev-parse --short HEAD).sqlite3
    if ! sqlite3 -readonly "$DB" ".backup '$copy'" || [ "$(sqlite3 "$copy" 'PRAGMA quick_check;')" != ok ]; then
        echo "Could not copy the database: stopping before the migrations, without reloading the app" >&2
        exit 1
    fi
    gzip "$copy"
    echo "Database copied to $copy.gz"
    # The names start with the date: newest first, keep the first $KEEP_COPIES
    ls -1r "$BACKUPS"/pre-migrate-*.sqlite3.gz | tail -n +$((KEEP_COPIES + 1)) | xargs -r rm --
fi
"$VENV/bin/python" manage.py migrate --noinput
"$VENV/bin/python" manage.py collectstatic --noinput -v0
if [ "$("$VENV/bin/gunicorn" --version)" = "$gunicorn_before" ]; then
    # Graceful reload: the socket stays open, so requests wait for the new workers instead of failing.
    # Starts the service instead if it isn't running.
    sudo systemctl reload-or-restart blog
else
    # The master process keeps running the Gunicorn it started with: only a restart picks up the new one
    sudo systemctl restart blog
fi
echo "Deployed $(git rev-parse --short HEAD)"
