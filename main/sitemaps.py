from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    def items(self):
        return ['main:index', 'main:about', 'main:cv', 'main:contact', 'main:privacy']

    def location(self, item):
        return reverse(item)
