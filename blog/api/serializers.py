from babel.dates import format_date
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from blog.models import Category, Post


class CreatePostSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field='slug', queryset=Category.objects.all())

    class Meta:
        model = Post
        fields = [
            'title_es',
            'title_en',
            'body_es',
            'body_en',
            'description_es',
            'description_en',
            'category',
            'read_time',
            'cover',
        ]

    def create(self, validated_data):
        validated_data['slug'] = Post.unique_slug(validated_data['title_en'])
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
        fields = [
            'href',
            'cover_url',
            'title',
            'category_href',
            'category',
            'category_color',
            'description',
            'timestamp',
            'user_friendly_date',
            'read_time',
        ]

    def get_href(self, obj):
        return reverse('blog:post-detail', kwargs={'slug': obj.slug})

    def get_cover_url(self, obj):
        if obj.cover:
            return obj.cover.url
        return ''

    def get_title(self, obj):
        lang = self.context['request'].headers.get('X-Language')
        if lang == 'es':
            return obj.title_es
        return obj.title_en

    def get_category_href(self, obj):
        if not obj.category:
            return ''
        return reverse('blog:category-detail', kwargs={'slug': obj.category.slug})

    def get_category(self, obj):
        if not obj.category:
            return ''
        lang = self.context['request'].headers.get('X-Language')
        if lang == 'es':
            return obj.category.name_es
        return obj.category.name_en

    def get_category_color(self, obj):
        if not obj.category:
            return ''
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
        return format_date(obj.created, format='dd MMM, yyyy', locale=lang)

    def get_read_time(self, obj):
        return '{} {}'.format(obj.read_time, _('min read'))


class CategorySerializer(serializers.ModelSerializer):
    first_5_posts = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    href = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['first_5_posts', 'name', 'slug', 'color', 'href']

    def get_href(self, obj):
        return reverse('blog:category-detail', kwargs={'slug': obj.slug})

    def get_first_5_posts(self, obj):
        posts = obj.posts.filter(is_published=True).order_by('-updated')[:5]
        return SearchPostSerializer(posts, many=True, context=self.context).data

    def get_name(self, obj):
        lang = self.context['request'].headers.get('X-Language')
        if lang == 'es':
            return obj.name_es
        return obj.name_en
