"""Helpers shared by the apps' tests."""

import json
import re
from datetime import timedelta

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


def structured_data(response):
    """The page's JSON-LD block, parsed; None if it has none."""
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', response.content.decode(), re.DOTALL)
    return json.loads(match.group(1)) if match else None


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
    # `created` is auto_now_add, so it can only be moved after the insert
    Post.objects.filter(pk=post.pk).update(created=timezone.now() - timedelta(days=days_ago))
    post.refresh_from_db()
    return post
