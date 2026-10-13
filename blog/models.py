from django.db import models

from config.base_models import BaseModel
from django.urls import reverse
from django.utils import translation
from django.utils.text import slugify


class Category(BaseModel):
    name_es = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    color = models.CharField(max_length=120)
    sub_category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name()

    def name(self):
        lang = translation.get_language()
        if lang == 'es':
            return self.name_es
        return self.name_en

    def get_absolute_url(self):
        return reverse('blog:category-detail', kwargs={'slug': self.slug})


class Post(BaseModel):
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
        if not self.slug:
            self.slug = self.unique_slug(self.title_es or self.title_en)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post-detail', kwargs={'slug': self.slug})

    @classmethod
    def unique_slug(cls, title):
        base_slug = slugify(title)
        slug = base_slug
        counter = 1

        while cls.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    @property
    def cover_url(self):
        return self.cover.url if self.cover else ''

    def title(self):
        lang = translation.get_language()
        if lang == 'es':
            return self.title_es
        return self.title_en

    def description(self):
        lang = translation.get_language()
        if lang == 'es':
            return self.description_es
        return self.description_en

    def rendered_body(self):
        import markdown
        from markdown.extensions import codehilite, fenced_code, admonition, attr_list, tables
        lang = translation.get_language()
        body = ''
        if lang == 'es':
            body = self.body_es
        elif lang == 'en':
            body = self.body_en
        return markdown.markdown(
            body,
            extensions=[
                fenced_code.FencedCodeExtension(),
                codehilite.CodeHiliteExtension(css_class='highlight'),
                admonition.AdmonitionExtension(),
                attr_list.AttrListExtension(),
                tables.TableExtension(),
            ]
        )

