#!/usr/bin/env bash
# Nightly backup of the SQLite database and media files.
# Keeps the last $KEEP_DAYS days on the server and, when an rclone remote named "backup" is configured, copies them
# to Google Drive and keeps the last $REMOTE_KEEP_DAYS days there (docs/adr/0005-off-site-backups-to-google-drive.md).
# If a step fails, it emails ADMINS (in the app's .env) through the site's SMTP server.
set -euo pipefail

BASE=${BASE:-/srv/blog}
DEST=$BASE/backups
KEEP_DAYS=14
REMOTE=backup:blog-backups
REMOTE_KEEP_DAYS=30
STAMP=$(date +%F)

alert() {
    (cd "$BASE/app" && "$BASE/venv/bin/python" manage.py email_admins "Backup $STAMP failed" "$1") || true
}
trap 'alert "Line $LINENO failed with status $?: $BASH_COMMAND
Its output is in $DEST/backup.log on the server (deploy/README.md, step 8)."' ERR

# find needs a working directory the blog user can read, wherever the script is started from
cd "$BASE"
mkdir -p "$DEST"

# .backup is safe to run while the site is serving requests
sqlite3 "$BASE/data/db.sqlite3" ".backup '$DEST/db-$STAMP.sqlite3'"
gzip -f "$DEST/db-$STAMP.sqlite3"
tar -czf "$DEST/media-$STAMP.tar.gz" -C "$BASE" media

# Only this script's own copies: update.sh keeps its pre-migrate-* copies in the same folder and prunes them itself
find "$DEST" -maxdepth 1 -type f \( -name 'db-*.sqlite3.gz' -o -name 'media-*.tar.gz' \) -mtime +"$KEEP_DAYS" -delete

if ! command -v rclone >/dev/null || ! rclone listremotes | grep -q '^backup:$'; then
    echo "$(date '+%F %T') No rclone remote named \"backup\": this backup stays on the server only." >&2
    exit 0
fi

# Every local backup not on Drive yet, so a night that failed to upload is caught up the next one
rclone copy "$DEST" "$REMOTE" --include 'db-*.sqlite3.gz' --include 'media-*.tar.gz'
# Removed files go to Drive's trash, which empties itself after 30 days
rclone delete "$REMOTE" --min-age "${REMOTE_KEEP_DAYS}d"
echo "$(date '+%F %T') Backup $STAMP copied to $REMOTE"
