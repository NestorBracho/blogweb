# 2. A single free-tier VM instead of a PaaS

- **Status:** Accepted
- **Date:** 2026-09-28

## Context

The site used to run on AWS, on Lightsail with uploaded images on S3. For a personal site the goals are to pay
nothing, to control the whole stack, and to have a setup worth showing. Most PaaS free tiers either put the
application to sleep when it is idle or give it an ephemeral filesystem, which rules out SQLite
([ADR 1](0001-sqlite-in-production.md)) and images stored on local disk.

## Decision

Run everything on one Google Cloud `e2-micro` VM from the Always Free tier (Ubuntu 24.04 LTS, 1 GB of RAM plus
2 GB of swap): nginx in front of Gunicorn with two workers, managed by systemd. Oracle Cloud's Always Free
instances are documented as a fallback.

The server is hardened by default:

- The application runs as a dedicated `blog` user that can only write to its data and media directories
  (`ProtectSystem=full`, `ReadWritePaths`, `NoNewPrivileges` and `PrivateTmp` in
  [`deploy/gunicorn.service`](../../deploy/gunicorn.service)).
- Gunicorn listens on a Unix socket, not on a TCP port.
- Security updates are installed automatically with `unattended-upgrades`.
- The Django admin lives under a non-default URL (`ADMIN_URL`).

## Consequences

- It costs nothing while it stays within the free tier. Outbound traffic is the tightest limit, which is why
  Cloudflare caches static files and images ([ADR 3](0003-cloudflare-in-front-of-the-origin.md)).
- Operating system updates, backups and monitoring are my responsibility.
- The VM is a single point of failure, which is acceptable for a personal site. Recovering means creating a new VM
  following [`deploy/README.md`](../../deploy/README.md) and restoring the latest backup.
