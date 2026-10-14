from django.db import models
from django.db.models import Max, Q
from django.urls import reverse
from django.utils import translation
from django.utils.text import slugify

from config.base_models import BaseModel


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
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='posts', null=True, blank=True)
    read_time = models.IntegerField(default=0)

    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        # The only place slugs are made, whether a post comes from the admin, the API or draft_article
        if not self.slug:
            self.slug = self.unique_slug(self.title_en or self.title_es)

        super().save(*args, **kwargs)

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
    def cover_url(self):
        return self.cover.url if self.cover else ''

    def title(self):
        return self.translated('title')

    def description(self):
        return self.translated('description')

    def rendered_body(self):
        import markdown
        from markdown.extensions import admonition, attr_list, codehilite, fenced_code, tables

        return markdown.markdown(
            self.translated('body'),
            extensions=[
                fenced_code.FencedCodeExtension(),
                codehilite.CodeHiliteExtension(css_class='highlight'),
                admonition.AdmonitionExtension(),
                attr_list.AttrListExtension(),
                tables.TableExtension(),
            ],
        )
