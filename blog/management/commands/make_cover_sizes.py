from django.core.management.base import BaseCommand

from blog.models import Post


class Command(BaseCommand):
    help = (
        "Make every post's cover at the sizes in blog/covers.py. New covers get them when saved: run this for covers "
        'saved before, or after changing the sizes. Sizes that already exist are not made again.'
    )

    def handle(self, *args, **options):
        for post in Post.objects.exclude(cover='').exclude(cover=None):
            post.update_cover_sizes()
            if post.cover_sizes:
                self.stdout.write(f'{post.slug}: {", ".join(post.cover_sizes["paths"])}')
            else:
                self.stderr.write(f'{post.slug}: could not read {post.cover.name}, the original stays in use')
