from django.urls import reverse

from config.sitemaps import TranslatedSitemap

from . import cases, services


class StaticViewSitemap(TranslatedSitemap):
    def items(self):
        return ['main:index', 'main:how-i-work', 'main:about', 'main:cv', 'main:contact', 'main:privacy']

    def location(self, item):
        return reverse(item)


class CaseSitemap(TranslatedSitemap):
    """The cases the site shows: in production, only the published ones."""

    def items(self):
        return cases.visible_cases()


class ServiceSitemap(TranslatedSitemap):
    def items(self):
        return services.SERVICES
