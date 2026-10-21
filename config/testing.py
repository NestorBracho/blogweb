"""Helpers shared by the apps' tests."""

import json
import re

from django.core.cache import cache
from django.urls import reverse
from django.utils import translation


def reverse_in(language, viewname, *args, **kwargs):
    """The URL of a page in one language: /en/… or /es/….

    Tests that check a language ask for it explicitly: plain reverse() follows the active language, which
    LocaleMiddleware leaves set to that of the last request.
    """
    with translation.override(language):
        return reverse(viewname, args=args, kwargs=kwargs)


def structured_data(response):
    """The page's JSON-LD block, parsed; None if it has none."""
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', response.content.decode(), re.DOTALL)
    return json.loads(match.group(1)) if match else None


class EmptyCacheMixin:
    """Each test starts and ends with an empty cache.

    The rate limits count requests in the cache (config/throttling.py), and every test client has the same address.
    """

    def setUp(self):
        super().setUp()
        cache.clear()
        self.addCleanup(cache.clear)
