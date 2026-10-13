from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse
from openai import OpenAI, OpenAIError

from blog.drafting import DraftingError, generate_cover, save_draft, write_article
from blog.models import Category


class Command(BaseCommand):
    help = 'Draft a bilingual post about a topic with OpenAI. It is saved unpublished, to be reviewed in the admin.'

    def add_arguments(self, parser):
        parser.add_argument('topic')
        parser.add_argument('--category', default='programming', help='category slug (default: programming)')
        parser.add_argument('--no-cover', action='store_true', help='do not generate a cover image')

    def handle(self, *args, **options):
        if not settings.OPENAI_API_KEY:
            raise CommandError('Set OPENAI_API_KEY to draft articles.')
        category = self.get_category(options['category'])
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        try:
            post = save_draft(write_article(client, options['topic']), category)
        except (DraftingError, OpenAIError) as error:
            raise CommandError(f'Could not draft the article: {error}') from error

        if not options['no_cover']:
            try:
                generate_cover(client, post)
            except OpenAIError as error:
                self.stdout.write(self.style.WARNING(f'Saved the draft without a cover: {error}'))

        admin_url = reverse('admin:blog_post_change', args=[post.pk])
        self.stdout.write(self.style.SUCCESS(f'Draft "{post.title_en}" saved. Review it at {admin_url}'))

    def get_category(self, slug):
        try:
            return Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            available = ', '.join(Category.objects.order_by('slug').values_list('slug', flat=True))
            raise CommandError(f'Unknown category "{slug}". Available: {available}') from None
