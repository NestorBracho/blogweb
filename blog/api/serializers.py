from rest_framework import serializers

from blog.models import Category, Post


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


class CategorySerializer(serializers.ModelSerializer):
    """A category, named in the active language."""

    name = serializers.CharField(read_only=True)
    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = Category
        fields = ['slug', 'name', 'color', 'url']


class PostListSerializer(serializers.ModelSerializer):
    """A post in the active language, as lists show it. Raw data: clients format dates and times themselves."""

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    category = CategorySerializer(read_only=True)
    # The cover at each size in blog/covers.py, by name
    cover_urls = serializers.DictField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = Post
        # read_time is in minutes; dates are ISO 8601. published_at is when readers first got the post
        fields = [
            'id',
            'slug',
            'url',
            'title',
            'description',
            'category',
            'cover_urls',
            'read_time',
            'published_at',
            'created',
            'updated',
        ]


class PostDetailSerializer(PostListSerializer):
    """A whole post: adds its body, in Markdown, and whether it is published (staff can read drafts)."""

    body = serializers.SerializerMethodField()

    class Meta(PostListSerializer.Meta):
        fields = [*PostListSerializer.Meta.fields, 'body', 'is_published']

    def get_body(self, obj):
        return obj.translated('body')


class CategoryWithPostsSerializer(CategorySerializer):
    """A category and its latest published posts (CategoryQuerySet.with_latest_posts)."""

    latest_posts = PostListSerializer(many=True, read_only=True)

    class Meta(CategorySerializer.Meta):
        fields = [*CategorySerializer.Meta.fields, 'latest_posts']
