from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from blog.models import Category, Post
from main.templatetags.main_tags import localized_date


class PostWriteSerializer(serializers.ModelSerializer):
    """
    Staff only: a post in both languages. New posts are drafts unless `is_published` is sent. The response carries
    the `id` to edit the post with and the `slug`, which Post.save() makes from the English title.
    """

    category = serializers.SlugRelatedField(slug_field='slug', queryset=Category.objects.all())

    class Meta:
        model = Post
        fields = [
            'id',
            'slug',
            'title_es',
            'title_en',
            'body_es',
            'body_en',
            'description_es',
            'description_en',
            'category',
            'read_time',
            'cover',
            'is_published',
        ]
        read_only_fields = ['id', 'slug', 'read_time']


class SearchPostSerializer(serializers.ModelSerializer):
    """A published post in the active language, shaped for the front-end templates."""

    href = serializers.CharField(source='get_absolute_url', read_only=True)
    cover_url = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    category_href = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    category_color = serializers.SerializerMethodField()
    description = serializers.CharField(read_only=True)
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

    def get_category_href(self, obj):
        return obj.category.get_absolute_url() if obj.category else ''

    def get_category(self, obj):
        return obj.category.name() if obj.category else ''

    def get_category_color(self, obj):
        return obj.category.color if obj.category else ''

    def get_timestamp(self, obj):
        return obj.created.isoformat()

    def get_user_friendly_date(self, obj):
        return localized_date(obj.created)

    def get_read_time(self, obj):
        return '{} {}'.format(obj.read_time, _('min read'))


class CategorySerializer(serializers.ModelSerializer):
    first_5_posts = serializers.SerializerMethodField()
    name = serializers.CharField(read_only=True)
    href = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = Category
        fields = ['first_5_posts', 'name', 'slug', 'color', 'href']

    def get_first_5_posts(self, obj):
        posts = obj.posts.filter(is_published=True).select_related('category').order_by('-updated')[:5]
        return SearchPostSerializer(posts, many=True, context=self.context).data
