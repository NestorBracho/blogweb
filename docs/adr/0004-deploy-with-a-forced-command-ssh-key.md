# 4. Deploying from CI with a forced-command SSH key

- **Status:** Accepted
- **Date:** 2026-09-28

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
- [`deploy/update.sh`](../../deploy/update.sh) fast-forwards to `main`, installs dependencies, runs migrations,
  collects static files and restarts the service. The `blog` user may only run that one `systemctl restart`
  through sudo.
- A health check fails the job unless the site answers `200` after the restart.
- Deploys never overlap (a concurrency group with no cancellation).

## Consequences

- A leaked key can only redeploy what is already on `main`.
- There is no automatic rollback: rolling back means reverting the change on `main`, which deploys again.
- Migrations run while the previous version is still serving requests, so they must stay compatible with it.
- Gunicorn is restarted rather than gracefully reloaded, so each deploy causes a short interruption, which is
  acceptable for this site.
