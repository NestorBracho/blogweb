from config.sitemaps import TranslatedSitemap

from .models import Category, Post


class PostSitemap(TranslatedSitemap):
    def items(self):
        return Post.objects.filter(is_published=True).order_by('-created')

    def lastmod(self, obj):
        return obj.updated


class CategorySitemap(TranslatedSitemap):
    def items(self):
        return Category.objects.with_published_posts().order_by('slug')
