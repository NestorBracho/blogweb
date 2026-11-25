from django.urls import reverse

from config.sitemaps import TranslatedSitemap

from .models import Category, Post


class BlogSitemap(TranslatedSitemap):
    """The list of posts. Only its first page: the others are reached through "Load more"."""

    def items(self):
        return ['blog:post-list']

    def location(self, item):
        return reverse(item)


class PostSitemap(TranslatedSitemap):
    def items(self):
        # Posts kept out of search results stay out of here too
        return Post.objects.published().exclude(noindex=True).order_by('-published_at')

    def lastmod(self, obj):
        # When the text changed, not any save
        return obj.content_modified


class CategorySitemap(TranslatedSitemap):
    def items(self):
        return Category.objects.with_published_posts().order_by('slug')
