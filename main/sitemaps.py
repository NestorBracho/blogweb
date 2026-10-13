from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    def items(self):
        return ['main:index', 'main:about', 'main:contact']

    def location(self, item):
        return reverse(item)
