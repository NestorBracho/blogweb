"""Helpers shared by the apps' tests."""

from django.urls import reverse
from django.utils import translation


def reverse_in(language, viewname, *args, **kwargs):
    """The URL of a page in one language: /en/… or /es/….

    Tests that check a language ask for it explicitly: plain reverse() follows the active language, which
    LocaleMiddleware leaves set to that of the last request.
    """
    with translation.override(language):
        return reverse(viewname, args=args, kwargs=kwargs)
