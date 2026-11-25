"""Helpers shared by the apps' tests."""

import json
import re
from datetime import timedelta

from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone, translation

from blog.models import Category, Post


def reverse_in(language, viewname, *args, **kwargs):
    """The URL of a page in one language: /en/… or /es/….

    Tests that check a language ask for it explicitly: plain reverse() follows the active language, which
    LocaleMiddleware leaves set to that of the last request.
    """
    with translation.override(language):
        return reverse(viewname, args=args, kwargs=kwargs)


JSON_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)


def structured_data(response):
    """The page's first JSON-LD block, its main entity, parsed; None if it has none."""
    match = JSON_LD.search(response.content.decode())
    return json.loads(match.group(1)) if match else None


def structured_data_blocks(response):
    """Every JSON-LD block of the page, parsed, in order."""
    return [json.loads(block) for block in JSON_LD.findall(response.content.decode())]


def structured_data_of_type(response, schema_type):
    """The page's JSON-LD block of that @type; None if it has none."""
    return next((block for block in structured_data_blocks(response) if block.get('@type') == schema_type), None)


# Data migrations already seed real categories, so tests use their own slugs
def create_category(slug='test-topic', **kwargs):
    fields = {'name_es': slug, 'name_en': slug, 'slug': slug, 'color': '#ae00ee', **kwargs}
    return Category.objects.create(**fields)


def create_post(title, days_ago=0, **kwargs):
    fields = {
        'title_es': title,
        'title_en': title,
        'body_es': 'Cuerpo',
        'body_en': 'Body',
        'description_es': 'Descripción',
        'description_en': 'Description',
        'is_published': True,
        **kwargs,
    }
    post = Post.objects.create(**fields)
    # `created` is auto_now_add, so it can only be moved after the insert. Published posts came out that same day, and
    # their text hasn't changed since.
    when = timezone.now() - timedelta(days=days_ago)
    published_at = when if post.published_at else None
    Post.objects.filter(pk=post.pk).update(created=when, published_at=published_at, content_updated=when)
    post.refresh_from_db()
    return post


class EmptyCacheMixin:
    """Each test starts and ends with an empty cache.

    The rate limits count requests in the cache (config/throttling.py), and every test client has the same address.
    """

    def setUp(self):
        super().setUp()
        cache.clear()
        self.addCleanup(cache.clear)
