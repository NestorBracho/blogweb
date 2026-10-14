from django.contrib.sitemaps import Sitemap

from .models import Category, Post


class PostSitemap(Sitemap):
    def items(self):
        return Post.objects.filter(is_published=True).order_by('-created')

    def lastmod(self, obj):
        return obj.updated


class CategorySitemap(Sitemap):
    def items(self):
        return Category.objects.with_published_posts().order_by('slug')
