#!/usr/bin/env bash
# Deploy a commit of main and reload the app. Run on the server as the "blog" user.
#
# GitHub Actions asks for the commit its run checked. Its key's forced command runs this script whatever the client
# asks for, and sshd hands what it asked for over in SSH_ORIGINAL_COMMAND
# (docs/adr/0004-deploy-with-a-forced-command-ssh-key.md). Without a commit, as when run by hand, it deploys the
# latest one on main.
#
# A deploy runs the copy of this script it started with: a change to it takes effect from the next deploy.
set -euo pipefail

VENV=/srv/blog/venv
DB=/srv/blog/data/db.sqlite3
BACKUPS=/srv/blog/backups
# Copies of the database taken before migrating
KEEP_COPIES=5

cd /srv/blog/app
git fetch --quiet origin main

commit=${SSH_ORIGINAL_COMMAND:-}
if [ -z "$commit" ]; then
    commit=$(git rev-parse origin/main)
elif [[ ! $commit =~ ^[0-9a-f]{40}$ ]]; then
    echo "Expected the full hash of a commit, got: $commit" >&2
    exit 1
elif ! git merge-base --is-ancestor "$commit" origin/main; then
    echo "$commit is not on main" >&2
    exit 1
fi

# Re-running an older workflow, or deploying by hand meanwhile, must not take the site back
if [ "$commit" != "$(git rev-parse HEAD)" ] && git merge-base --is-ancestor "$commit" HEAD; then
    echo "Already on $(git rev-parse --short HEAD), which includes $(git rev-parse --short "$commit"): nothing to do"
    exit 0
fi

# Until the migrations run, the database still matches the code being served. If the deploy stops before them, put
# that code and its requirements back: a later restart (systemd, the 04:00 reboot) must not start new code on an
# unmigrated database.
previous=$(git rev-parse HEAD)
roll_back() {
    echo "$1: going back to $(git rev-parse --short "$previous"), without migrating or reloading the app" >&2
    if ! git reset --hard --quiet "$previous" || ! "$VENV/bin/pip" install -q -r requirements.txt; then
        echo "Could not go back to $(git rev-parse --short "$previous") either: fix it by hand before the app restarts" >&2
    fi
    exit 1
}

gunicorn_before=$("$VENV/bin/gunicorn" --version)
git merge --ff-only --quiet "$commit"
"$VENV/bin/pip" install -q -r requirements.txt || roll_back "Could not install the requirements"

# Copy the database before migrations change it, so a migration that goes wrong can be undone (deploy/README.md).
# -readonly: if the database isn't there, fail instead of copying a new empty one.
if ! "$VENV/bin/python" manage.py migrate --check >/dev/null; then
    copy=$BACKUPS/pre-migrate-$(date +%F-%H%M%S)-$(git rev-parse --short HEAD).sqlite3
    if ! sqlite3 -readonly "$DB" ".backup '$copy'" || [ "$(sqlite3 "$copy" 'PRAGMA quick_check;')" != ok ]; then
        rm -f "$copy"
        roll_back "Could not copy the database"
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
