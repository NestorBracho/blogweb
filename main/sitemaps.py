from django.urls import reverse

from config.sitemaps import TranslatedSitemap

from . import cases


class StaticViewSitemap(TranslatedSitemap):
    def items(self):
        return ['main:index', 'main:about', 'main:cv', 'main:contact', 'main:privacy']

    def location(self, item):
        return reverse(item)


class CaseSitemap(TranslatedSitemap):
    """The cases the site shows: in production, only those whose every field is confirmed."""

    def items(self):
        return cases.visible_cases()
