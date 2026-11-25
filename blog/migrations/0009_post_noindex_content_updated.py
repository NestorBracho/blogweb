from django.db import migrations, models
from django.db.models import F

# Off what the site is about (Django, APIs, AI agents): kept published, out of search results. The admin's "Noindex"
# checkbox does the same for any other post.
OFF_STRATEGY_POSTS = ['special-vs-general-relativity-whats-the-difference']


def date_content_and_flag_posts(apps, schema_editor):
    """Existing posts last changed when they were last saved; the off-strategy ones leave search results, the rest
    stay in them."""
    Post = apps.get_model('blog', 'Post')
    Post.objects.filter(content_updated__isnull=True).update(content_updated=F('updated'))
    # A no-op where the post doesn't exist (a laptop's database, tests)
    Post.objects.filter(slug__in=OFF_STRATEGY_POSTS).update(noindex=True)
    Post.objects.filter(noindex__isnull=True).update(noindex=False)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0008_post_published_at'),
    ]

    # Only adds nullable columns without defaults (ALTER TABLE ... ADD COLUMN, no table rebuild): the code still
    # running while a deploy migrates doesn't know them and keeps reading and writing the table as before.
    operations = [
        migrations.AddField(
            model_name='post',
            name='noindex',
            field=models.BooleanField(blank=True, help_text='Keep this post out of search results. It stays published and reachable by its address.', null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='content_updated',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        # Going back drops the columns, and their values with them
        migrations.RunPython(date_content_and_flag_posts, migrations.RunPython.noop),
    ]
