#!/usr/bin/env bash
# Nightly backup of the SQLite database and media files.
# Keeps the last $KEEP_DAYS days locally and, if an rclone remote named
# "backup" is configured, copies them off the server too.
set -euo pipefail

BASE=/srv/blog
DEST=$BASE/backups
KEEP_DAYS=14
STAMP=$(date +%F)

mkdir -p "$DEST"

# .backup is safe to run while the site is serving requests
sqlite3 "$BASE/data/db.sqlite3" ".backup '$DEST/db-$STAMP.sqlite3'"
gzip -f "$DEST/db-$STAMP.sqlite3"
tar -czf "$DEST/media-$STAMP.tar.gz" -C "$BASE" media

find "$DEST" -type f -mtime +"$KEEP_DAYS" -delete

if command -v rclone >/dev/null && rclone listremotes | grep -q '^backup:$'; then
    rclone copy "$DEST" backup:blog-backups --max-age 48h
fi
