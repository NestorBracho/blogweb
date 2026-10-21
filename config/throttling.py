"""
How often one visitor may call the API or send the forms. The rates are in REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].

The counts live in the default cache, which is kept in memory by each Gunicorn worker: a visitor whose requests are
spread over N workers can get up to N times a rate. That is enough to stop a script hammering the site, without a
shared cache to run on the server.
"""

from rest_framework import throttling
from rest_framework.permissions import SAFE_METHODS


def client_ip(request):
    """
    The visitor's IP address.

    The VM's firewall only lets Cloudflare reach the site (docs/adr/0003-cloudflare-in-front-of-the-origin.md), and
    Cloudflare sets CF-Connecting-IP on every request it forwards, replacing any value the visitor sent; nginx passes
    it on as it is. So, unlike X-Forwarded-For, which anyone can add addresses to, it can be trusted here. Without it
    (runserver, tests) this is whoever connected to Django.
    """
    return request.META.get('HTTP_CF_CONNECTING_IP') or request.META.get('REMOTE_ADDR', '')


class ClientIPMixin:
    def get_ident(self, request):
        return client_ip(request)


class AnonRateThrottle(ClientIPMixin, throttling.AnonRateThrottle):
    """API requests from visitors who aren't signed in, per IP address."""


class UserRateThrottle(ClientIPMixin, throttling.UserRateThrottle):
    """API requests per signed-in account (staff), and per IP address for everyone else."""


class WriteRateThrottle(UserRateThrottle):
    """A tighter limit on creating, editing and deleting posts."""

    scope = 'write'

    def allow_request(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return super().allow_request(request, view)


class FormThrottle(ClientIPMixin, throttling.SimpleRateThrottle):
    """Submissions of one of the site's forms (its scope) per IP address, signed in or not. Works in any Django view."""

    def __init__(self, scope):
        self.scope = scope
        super().__init__()

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}
