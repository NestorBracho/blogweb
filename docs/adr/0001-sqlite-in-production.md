# 1. SQLite in production

- **Status:** Accepted
- **Date:** 2026-09-27

## Context

This is a personal blog. Writes are rare (new posts from the admin, contact requests, newsletter sign-ups) and
almost every request is a read. It runs on a single VM with 1 GB of RAM ([ADR 2](0002-single-free-tier-vm.md)),
where a separate database server would compete for memory and add one more service to patch, tune and back up.

## Decision

Use SQLite as the production database, configured for a web server with several worker processes
([`config/settings.py`](../../config/settings.py)):

- `journal_mode=WAL`, so readers never wait for the writer, with `synchronous=NORMAL`, which is safe in WAL mode.
- `BEGIN IMMEDIATE` transactions and a 20-second busy timeout, so concurrent writes from different Gunicorn
  workers wait for the lock instead of failing with "database is locked".
- Nightly online backups with `sqlite3 .backup` ([`deploy/backup.sh`](../../deploy/backup.sh)), which produce a
  consistent copy while the site keeps serving requests.

## Consequences

- The whole database is one file: backing it up, restoring it or copying it to a laptop is trivial.
- There is no database server to run, secure or keep in memory.
- Writes are serialized. That is irrelevant at this traffic, but this setup cannot scale out to several
  application servers.
- The code only talks to the database through the ORM, so moving to PostgreSQL is a settings change plus a data
  migration. Reasons to do it: more than one application server, or lock waits showing up in the logs.
