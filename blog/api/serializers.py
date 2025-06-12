from rest_framework import serializers
from django.urls import reverse
from babel.dates import format_date
from django.utils.text import slugify
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _

from blog.models import Post, Category


class CreatePostSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field='slug', queryset=Category.objects.all())

    class Meta:
        model = Post
        fields = ['title_es', 'title_en', 'body_es', 'body_en', 'description_es',
                  'description_en', 'category', 'read_time', 'cover']

    def create(self, validated_data):
        validated_data['slug'] = slugify(validated_data['title_en'])

        validated_data['body_en'] = SafeString(validated_data['body_en'])

        validated_data['body_es'] = SafeString(validated_data['body_en'])
        return super().create(validated_data)


class SearchPostSerializer(serializers.ModelSerializer):

    href = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    category_href = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    category_color = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()
    user_friendly_date = serializers.SerializerMethodField()
    read_time = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['href', 'cover_url', 'title', 'category_href', 'category', 'category_color',
                  'description', 'timestamp', 'user_friendly_date', 'read_time']

    def get_href(self, obj):
        return reverse('blog:post-detail', kwargs={'slug': obj.slug})

    def get_cover_url(self, obj):
        return obj.cover.url

    def get_title(self, obj):
        lang = self.context['request'].headers.get('X-Language')
        if lang == 'es':
            return obj.title_es
        return obj.title_en

    def get_category_href(self, obj):
        return reverse('blog:category-detail', kwargs={'slug': obj.category.slug})

    def get_category(self, obj):
        lang = self.context['request'].headers.get('X-Language')
        if lang == 'es':
            return obj.category.name_es
        return obj.category.name_en

    def get_category_color(self, obj):
        return obj.category.color

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
