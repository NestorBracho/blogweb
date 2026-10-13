# 3. Cloudflare in front of the origin

- **Status:** Accepted
- **Date:** 2026-09-28

## Context

The VM has little CPU and a small monthly allowance of outbound traffic ([ADR 2](0002-single-free-tier-vm.md)).
The site must be served over HTTPS, and I would rather not renew certificates or expose the server directly to
every visitor.

## Decision

Proxy all traffic through Cloudflare's free plan with SSL/TLS set to **Full (strict)**:

- Visitors connect to Cloudflare, which terminates TLS and caches static files and images.
- Cloudflare connects to nginx over HTTPS using a Cloudflare origin certificate. The certificate is issued from a
  CSR generated on the server, so its private key never leaves the machine.
- Django detects HTTPS from the `X-Forwarded-Proto` header set by nginx, redirects plain HTTP and sends HSTS.

## Consequences

- TLS, HTTP/2, caching and basic DDoS protection come at no cost, and the origin certificate is valid for 15
  years, so there are no renewals to automate.
- Most requests for static files and images never reach the VM, which keeps outbound traffic low.
- Only Cloudflare trusts the origin certificate. Moving away from Cloudflare means installing a publicly trusted
  certificate first.
- The protection only holds if the origin is reachable exclusively through Cloudflare: its IP address must stay
  private and the firewall should only accept web traffic from Cloudflare's IP ranges.
