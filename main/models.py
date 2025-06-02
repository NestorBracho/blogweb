from config import base_models as models
from django.utils import translation
from django.utils.text import slugify


class Category(models.Model):
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


class Post(models.Model):
    slug = models.SlugField(max_length=120, unique=True)
    title_es = models.CharField(max_length=60)
    title_en = models.CharField(max_length=60)
    body_es = models.TextField()
    body_en = models.TextField()
    description_es = models.CharField(max_length=160)
    description_en = models.CharField(max_length=160)
    cover = models.ImageField(upload_to='images/')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    read_time = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_title = self.title_es or self.title_en
            base_slug = slugify(base_title)
            slug = base_slug
            counter = 1

            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def title(self):
        lang = translation.get_language()
        if lang == 'es':
            return self.title_es
        return self.title_en

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
