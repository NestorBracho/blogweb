import logging
import math

from django.db import models
from django.db.models import Max, Prefetch, Q
from django.urls import reverse
from django.utils import translation
from django.utils.text import slugify
from PIL import Image

from config.base_models import BaseModel

from . import covers
from .rendering import render_markdown

logger = logging.getLogger(__name__)

WORDS_PER_MINUTE = 200


def estimate_read_time(text):
    """Minutes to read a text at an average pace, never less than one."""
    return max(1, math.ceil(len(text.split()) / WORDS_PER_MINUTE))


def content_language():
    """Language of the content to show: posts exist in Spanish and English, anything else falls back to English."""
    return 'es' if translation.get_language() == 'es' else 'en'


class TranslatedFieldsMixin:
    """For models that store each translatable field twice, as `<field>_es` and `<field>_en`."""

    def translated(self, field):
        return getattr(self, f'{field}_{content_language()}')


class CategoryQuerySet(models.QuerySet):
    def with_published_posts(self):
        """
        Categories readers can see: those with at least one published post. Empty ones stay in the admin, ready
        for future posts, and show up on their own once one is published. `latest_post` is the newest one's date.
        """
        latest_post = Max('posts__created', filter=Q(posts__is_published=True))
        return self.annotate(latest_post=latest_post).filter(latest_post__isnull=False)

    def with_latest_posts(self, count):
        """Gives each category a `latest_posts` list: its newest published posts, at most `count`, in one query."""
        posts = Post.objects.filter(is_published=True).order_by('-created')[:count]
        return self.prefetch_related(Prefetch('posts', queryset=posts, to_attr='latest_posts'))


class Category(TranslatedFieldsMixin, BaseModel):
    name_es = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    color = models.CharField(max_length=120)
    sub_category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, blank=True)

    objects = CategoryQuerySet.as_manager()

    def __str__(self):
        return self.name()

    def name(self):
        return self.translated('name')

    def get_absolute_url(self):
        return reverse('blog:category-detail', kwargs={'slug': self.slug})


class Post(TranslatedFieldsMixin, BaseModel):
    slug = models.SlugField(max_length=120, unique=True)
    title_es = models.CharField(max_length=60)
    title_en = models.CharField(max_length=60)
    body_es = models.TextField()
    body_en = models.TextField()
    description_es = models.CharField(max_length=160)
    description_en = models.CharField(max_length=160)
    cover = models.ImageField(upload_to='images/', blank=True, null=True)
    # The cover at each size in blog/covers.py: {'source': the cover they were made from, 'paths': {size: path}}
    cover_sizes = models.JSONField(default=dict, editable=False)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='posts', null=True, blank=True)
    # Minutes, worked out from the text on every save
    read_time = models.IntegerField(default=1, editable=False)

    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        # The only place slugs are made, whether a post comes from the admin, the API or draft_article
        if not self.slug:
            self.slug = self.unique_slug(self.title_en or self.title_es)
        # Both languages show the same figure, so use the longer text
        self.read_time = max(estimate_read_time(self.body_en), estimate_read_time(self.body_es))

        super().save(*args, **kwargs)

        # After saving, so a new upload is already in storage under its final name. Covers the admin, the API and
        # draft_article alike, and does nothing while the cover stays the same.
        if self.cover_sizes.get('source', '') != (self.cover.name or ''):
            self.update_cover_sizes()

    def update_cover_sizes(self):
        """Makes the cover at every size, deletes the sizes of the previous cover and records the new ones."""
        old_paths = set(self.cover_sizes.get('paths', {}).values())
        self.cover_sizes = {}
        if self.cover:
            try:
                self.cover_sizes = {'source': self.cover.name, 'paths': covers.make_sizes(self.cover, self.slug)}
            except (OSError, Image.DecompressionBombError):
                # An image Pillow can't read or a missing file: the post keeps working with the original cover
                logger.exception('Could not make the sizes of the cover %s', self.cover.name)
        for path in old_paths - set(self.cover_sizes.get('paths', {}).values()):
            self.cover.storage.delete(path)
        Post.objects.filter(pk=self.pk).update(cover_sizes=self.cover_sizes)

    def get_absolute_url(self):
        return reverse('blog:post-detail', kwargs={'slug': self.slug})

    @classmethod
    def unique_slug(cls, title):
        base_slug = slugify(title)
        slug = base_slug
        counter = 1

        while cls.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1

        return slug

    @property
    def cover_urls(self):
        """The cover's URL at each size, by name. The original stands in for any size that couldn't be made."""
        names = [*covers.SIZES, 'social']
        if not self.cover:
            return dict.fromkeys(names, '')
        paths = self.cover_sizes.get('paths', {})
        return {name: self.cover.storage.url(paths[name]) if name in paths else self.cover.url for name in names}

    def title(self):
        return self.translated('title')

    def description(self):
        return self.translated('description')

    def rendered_body(self):
        return render_markdown(self.translated('body'))
