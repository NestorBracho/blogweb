from django.urls import reverse

from config.sitemaps import TranslatedSitemap


class StaticViewSitemap(TranslatedSitemap):
    def items(self):
        return ['main:index', 'main:about', 'main:cv', 'main:contact', 'main:privacy']

    def location(self, item):
        return reverse(item)
