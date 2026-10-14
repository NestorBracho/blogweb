from django.contrib.syndication.views import Feed
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from .models import Post


class LatestPostsFeed(Feed):
    title = 'Nestor Bracho'
    link = reverse_lazy('main:index')
    description = _('Posts by Nestor Bracho, Senior Backend Engineer.')

    def items(self):
        return Post.objects.filter(is_published=True).order_by('-created')[:20]

    def item_title(self, item):
        return item.title()

    def item_description(self, item):
        return item.description()

    def item_pubdate(self, item):
        return item.created

    def item_updateddate(self, item):
        return item.updated
