# 5. Off-site backups to Google Drive

- **Status:** Accepted
- **Date:** 2026-10-14

## Context

[`deploy/backup.sh`](../../deploy/backup.sh) backs up the database and the uploaded images every night, but only to
the VM's own disk: losing the VM would lose the backups with it. [ADR 2](0002-single-free-tier-vm.md) accepts the VM
as a single point of failure because recovering means a new VM plus the latest backup, and that only holds if the
backup lives somewhere else.

The project has to stay free. A day's backup is small: about 50 KB for the compressed database and 6 MB for the
images.

## Decision

Copy the backups to Google Drive with rclone, which the server guide already installs, through a remote named
`backup`:

- The remote uses the `drive.file` scope, so the server can only see the files it created, not the rest of the
  Drive.
- Each night the script uploads every local backup that isn't on Drive yet, so a night that failed to upload is
  caught up the next one, and deletes those older than 30 days. Deleted files go to Drive's trash, which empties
  itself after another 30 days.
- Authorizing is a one-off step from a computer with a browser (`rclone authorize`). The server keeps the resulting
  refresh token in the `blog` user's rclone configuration.

Alternatives considered:

- **Google Cloud Storage's Always Free tier** (5 GB in the VM's region) would allow a key limited to one bucket and
  lifecycle rules. But it sits on the project's billing account, and getting the region, storage class or size
  wrong costs money.
- **Backblaze B2** (10 GB free) and **Cloudflare R2** (10 GB free, but it asks for a payment method) would mean
  another account and more keys to manage.

## Consequences

- It costs nothing, and no billing account is involved. Thirty days of backups take about 200 MB of the 15 GB that
  Google shares between Drive, Gmail and Photos.
- The token belongs to my personal Google account. If it is revoked, uploads fail and say so in
  `/srv/blog/backups/backup.log`, while the server keeps its local copies. Nothing raises an alert yet.
- Restoring is described in [`deploy/README.md`](../../deploy/README.md). A backup only counts once a restore from
  it has worked.
- Every night uploads a full archive of the images, unchanged ones included. At this size that doesn't matter; if
  the images grow, syncing `media/` would be cheaper.
