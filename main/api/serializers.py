from rest_framework import serializers
from django.urls import reverse
from babel.dates import format_date
from django.utils.translation import gettext_lazy as _

from main.models import Post


class PostSerializer(serializers.ModelSerializer):

    href = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    category_href = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()
    user_friendly_date = serializers.SerializerMethodField()
    read_time = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['href', 'cover_url', 'title', 'category_href', 'category',
                  'description', 'timestamp', 'user_friendly_date', 'read_time']

    def get_href(self, obj):
        return reverse('main:post-detail', kwargs={'slug': obj.slug})

    def get_cover_url(self, obj):
        return obj.cover.url

    def get_title(self, obj):
        lang = self.context['request'].headers.get('X-Language')
        if lang == 'es':
            return obj.title_es
        return obj.title_en

    def get_category_href(self, obj):
        return reverse('main:category-detail', kwargs={'slug': obj.category.slug})

    def get_category(self, obj):
        lang = self.context['request'].headers.get('X-Language')
        if lang == 'es':
            return obj.category.name_es
        return obj.category.name_en

    def get_description(self, obj):
        lang = self.context['request'].headers.get('X-Language')
        if lang == 'es':
            return obj.description_es
        return obj.description_en

    def get_timestamp(self, obj):
        return obj.created.isoformat()

    def get_user_friendly_date(self, obj):
        lang = self.context['request'].headers.get('X-Language')
        return format_date(obj.created, format="dd MMM, yyyy", locale=lang)

    def get_read_time(self, obj):
        return '{} {}'.format(obj.read_time, _('min read'))
