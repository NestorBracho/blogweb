# 4. Deploying from CI with a forced-command SSH key

- **Status:** Accepted
- **Date:** 2026-09-28
- **Updated:** 2026-10-15 (Gunicorn reloads gracefully instead of restarting), 2026-10-21 (the database is copied
  before migrations)

## Context

Deploying by hand (connect to the server, pull, migrate, collect static files, restart) is slow and easy to get
wrong. Automating it from GitHub Actions means storing an SSH key in GitHub, and an ordinary key would turn a
leaked secret into a shell on the production server.

## Decision

GitHub Actions deploys every push to `main` once the checks pass
([`.github/workflows/deploy.yml`](../../.github/workflows/deploy.yml)):

- It connects with a dedicated ed25519 key that the server restricts in `authorized_keys` with
  `restrict,command="/srv/blog/app/deploy/update.sh"`. Whatever the client asks for, the server runs the update
  script and nothing else: no shell, no port forwarding, no agent forwarding.
- The server's host key is pinned in a secret and checked strictly.
- [`deploy/update.sh`](../../deploy/update.sh) fast-forwards to `main`, installs dependencies, copies the database
  if there are migrations to run, runs them, collects static files and reloads Gunicorn gracefully, or restarts it
  when Gunicorn itself was upgraded. Through sudo, the `blog` user may only run those two `systemctl` commands on its
  own service.
- A health check fails the job unless the site answers `200` after the deploy.
- Deploys never overlap (a concurrency group with no cancellation).

## Consequences

- A leaked key can only redeploy what is already on `main`.
- There is no automatic rollback: rolling back means reverting the change on `main`, which deploys again.
- Migrations run while the previous version is still serving requests, so they must stay compatible with it. A copy
  of the database taken just before them (the last five are kept) undoes one that goes wrong.
- Deploys don't drop requests: on a reload (`HUP`) Gunicorn keeps its socket open, starts workers with the new code
  and lets the old ones finish their requests. Until 2026-10-15 every deploy restarted it and the site answered
  `502` for a few seconds.
- A deploy that upgrades Gunicorn still restarts it, because the master process keeps running the version it started
  with, so that one causes the short interruption.
