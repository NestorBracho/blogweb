import base64
from datetime import timedelta
from io import StringIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock
from urllib.parse import quote

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from openai import OpenAIError

from .drafting import ArticleDraft
from .models import Category, Post


# Data migrations already seed real categories, so tests use their own slugs
def create_category(slug='test-topic', **kwargs):
    fields = {'name_es': slug, 'name_en': slug, 'slug': slug, 'color': '#ae00ee', **kwargs}
    return Category.objects.create(**fields)


def create_post(title, days_ago=0, **kwargs):
    fields = {
        'title_es': title,
        'title_en': title,
        'body_es': 'Cuerpo',
        'body_en': 'Body',
        'description_es': 'Descripción',
        'description_en': 'Description',
        'is_published': True,
        **kwargs,
    }
    post = Post.objects.create(**fields)
    # `created` is auto_now_add, so it can only be moved after the insert
    Post.objects.filter(pk=post.pk).update(created=timezone.now() - timedelta(days=days_ago))
    post.refresh_from_db()
    return post


class PostDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = create_category()
        cls.older = create_post('Older', days_ago=4, category=cls.category)
        cls.draft = create_post('Draft', days_ago=3, category=cls.category, is_published=False)
        cls.post = create_post('Current', days_ago=2, category=cls.category)
        cls.newer = create_post('Newer', days_ago=1, category=create_category('other-topic'))

    def get(self, post):
        return self.client.get(post.get_absolute_url())

    def test_renders_published_post(self):
        response = self.get(self.post)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.get_absolute_url())

    def test_post_without_category_renders(self):
        post = create_post('No category', category=None)

        response = self.get(post)

        self.assertEqual(response.status_code, 200)

    def test_unpublished_post_is_not_found(self):
        response = self.get(self.draft)

        self.assertEqual(response.status_code, 404)

    def test_navigation_skips_drafts(self):
        response = self.get(self.post)

        self.assertEqual(response.context['previous_post'], self.older)
        self.assertEqual(response.context['next_post'], self.newer)

    def test_related_posts_share_the_category(self):
        response = self.get(self.post)

        self.assertEqual(list(response.context['related_posts']), [self.older])

    def test_share_links_point_to_the_post(self):
        response = self.get(self.post)

        post_url = quote(f'http://testserver{self.post.get_absolute_url()}', safe='')
        self.assertContains(response, f'url={post_url}')
        self.assertNotContains(response, 'coderon')

    def test_social_image_is_an_absolute_url(self):
        response = self.get(self.post)

        self.assertContains(response, '<meta property="og:image" content="http://testserver/static/')


class CategoryDetailViewTests(TestCase):
    def test_post_cards_link_to_the_category_slug(self):
        category = create_category()
        create_post('Post', category=category)

        response = self.client.get(category.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="{category.get_absolute_url()}"')
        self.assertNotContains(response, str(category.pk))

    def test_unknown_category_is_not_found(self):
        response = self.client.get(reverse('blog:category-detail', kwargs={'slug': 'missing'}))

        self.assertEqual(response.status_code, 404)


class CategoryDeletionTests(TestCase):
    def test_deleting_a_category_keeps_its_posts(self):
        category = create_category()
        post = create_post('Post', category=category)

        category.delete()

        post.refresh_from_db()
        self.assertIsNone(post.category)


class FeedTests(TestCase):
    def test_feed_lists_published_posts_only(self):
        create_post('Published post')
        create_post('Draft post', is_published=False)

        response = self.client.get(reverse('blog:feed'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('application/rss+xml', response['Content-Type'])
        self.assertContains(response, 'Published post')
        self.assertNotContains(response, 'Draft post')


class SitemapTests(TestCase):
    def test_sitemap_lists_pages_and_published_content(self):
        published = create_post('Published', category=create_category('other-topic'))
        draft = create_post('Draft', is_published=False, category=create_category('drafts-only'))

        response = self.client.get(reverse('sitemap'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'<loc>http://testserver{reverse("main:about")}</loc>')
        self.assertContains(response, f'<loc>http://testserver{published.get_absolute_url()}</loc>')
        self.assertContains(response, f'<loc>http://testserver{published.category.get_absolute_url()}</loc>')
        self.assertNotContains(response, draft.get_absolute_url())
        self.assertNotContains(response, draft.category.get_absolute_url())


class PostAPITests(TestCase):
    url = reverse_lazy('blog:api:post-list')

    def test_lists_published_posts_a_page_at_a_time(self):
        for number in range(5):
            create_post(f'Post {number}', days_ago=number)
        create_post('Draft', is_published=False)

        response = self.client.get(self.url)

        page = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(page['count'], 5)
        self.assertEqual([post['title'] for post in page['results']], ['Post 0', 'Post 1', 'Post 2', 'Post 3'])

    def test_searches_in_the_requested_language(self):
        create_post('Black holes', title_es='Agujeros negros')

        spanish = self.client.get(self.url, {'search': 'agujeros'}, headers={'X-Language': 'es'})
        english = self.client.get(self.url, {'search': 'agujeros'}, headers={'X-Language': 'en'})

        self.assertEqual([post['title'] for post in spanish.json()], ['Agujeros negros'])
        self.assertEqual(english.json(), [])

    def test_language_header_applies_to_the_whole_response(self):
        create_post('Black holes', title_es='Agujeros negros', read_time=3)

        # The site defaults to Spanish, but the header asks for English
        response = self.client.get(self.url, headers={'X-Language': 'en'})

        post = response.json()['results'][0]
        self.assertEqual((post['title'], post['read_time']), ('Black holes', '3 min read'))
        self.assertIn('X-Language', response['Vary'])

    def test_language_follows_the_site_without_the_header(self):
        create_post('Black holes', title_es='Agujeros negros', read_time=3)

        response = self.client.get(self.url, headers={'Accept-Language': 'es'})

        post = response.json()['results'][0]
        self.assertEqual((post['title'], post['read_time']), ('Agujeros negros', '3 min de lectura'))

    def test_anonymous_users_cannot_create_posts(self):
        response = self.client.post(self.url, {'title_en': 'Spam'})

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Post.objects.filter(title_en='Spam').exists())

    def test_staff_can_create_draft_posts(self):
        self.client.force_login(get_user_model().objects.create_user(username='editor', is_staff=True))
        category = create_category()

        response = self.client.post(
            self.url,
            {
                'title_es': 'Hola mundo',
                'title_en': 'Hello world',
                'body_es': 'Cuerpo',
                'body_en': 'Body',
                'description_es': 'Descripción',
                'description_en': 'Description',
                'category': category.slug,
                'read_time': 3,
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertFalse(Post.objects.get(slug='hello-world').is_published)


class CategoryAPITests(TestCase):
    def test_lists_categories_with_their_latest_published_posts(self):
        category = create_category()
        create_post('Old', category=category)
        create_post('New', category=category)
        create_post('Draft', category=category, is_published=False)
        create_category('empty-topic')

        response = self.client.get(reverse('blog:api:categories'))

        categories = response.json()['results']
        self.assertEqual([category['slug'] for category in categories], ['test-topic'])
        self.assertEqual([post['title'] for post in categories[0]['first_5_posts']], ['New', 'Old'])


def parsed_completion(draft=None, refusal=None):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(parsed=draft, refusal=refusal))])


@override_settings(OPENAI_API_KEY='test-key', OPENAI_MODEL='test-model')
class DraftArticleCommandTests(TestCase):
    draft = ArticleDraft(
        title_en='Ownership in Rust',
        title_es='Propiedad en Rust',
        description_en='How Rust frees memory without a garbage collector.',
        description_es='Cómo Rust libera memoria sin recolector de basura.',
        body_en='word ' * 450,
        body_es='palabra ' * 450,
    )

    def setUp(self):
        self.category = create_category()
        # No request ever leaves the test: the command gets this fake client instead of a real one
        self.openai = mock.MagicMock()
        self.openai.beta.chat.completions.parse.return_value = parsed_completion(self.draft)
        self.openai.images.generate.return_value = SimpleNamespace(
            data=[SimpleNamespace(b64_json=base64.b64encode(b'image').decode())]
        )
        patcher = mock.patch('blog.management.commands.draft_article.OpenAI', return_value=self.openai)
        patcher.start()
        self.addCleanup(patcher.stop)

    def draft_article(self, *args):
        output = StringIO()
        call_command('draft_article', 'Rust ownership', '--category', self.category.slug, *args, stdout=output)
        return output.getvalue()

    def test_saves_an_unpublished_bilingual_draft(self):
        output = self.draft_article('--no-cover')

        post = Post.objects.get(slug='ownership-in-rust')
        self.assertFalse(post.is_published)
        self.assertEqual(post.category, self.category)
        self.assertEqual((post.title_es, post.body_es), (self.draft.title_es, self.draft.body_es))
        self.assertEqual(post.read_time, 3)
        self.assertIn(reverse('admin:blog_post_change', args=[post.pk]), output)
        self.openai.images.generate.assert_not_called()

    def test_asks_for_structured_output(self):
        self.draft_article('--no-cover')

        request = self.openai.beta.chat.completions.parse.call_args.kwargs
        self.assertEqual(request['model'], 'test-model')
        self.assertIs(request['response_format'], ArticleDraft)
        self.assertIn('Rust ownership', request['messages'][-1]['content'])

    def test_shortens_texts_that_do_not_fit_their_columns(self):
        self.openai.beta.chat.completions.parse.return_value = parsed_completion(
            self.draft.model_copy(update={'title_en': 'A' * 80, 'description_es': 'B' * 200})
        )

        self.draft_article('--no-cover')

        post = Post.objects.get(category=self.category)
        self.assertEqual(len(post.title_en), 60)
        self.assertEqual(len(post.description_es), 160)

    def test_attaches_a_generated_cover(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.draft_article()

            post = Post.objects.get(slug='ownership-in-rust')
            with post.cover.open('rb') as cover:
                self.assertEqual(cover.read(), b'image')

    def test_keeps_the_draft_when_the_cover_fails(self):
        self.openai.images.generate.side_effect = OpenAIError('Image service unavailable')

        output = self.draft_article()

        self.assertFalse(Post.objects.get(slug='ownership-in-rust').cover)
        self.assertIn('without a cover', output)

    def test_reports_a_refusal_without_saving_anything(self):
        self.openai.beta.chat.completions.parse.return_value = parsed_completion(refusal='I cannot write that.')

        with self.assertRaisesMessage(CommandError, 'I cannot write that.'):
            self.draft_article()

        self.assertFalse(Post.objects.filter(category=self.category).exists())

    def test_rejects_an_unknown_category(self):
        with self.assertRaisesMessage(CommandError, 'Unknown category "missing"'):
            call_command('draft_article', 'Rust ownership', '--category', 'missing')

        self.openai.beta.chat.completions.parse.assert_not_called()

    @override_settings(OPENAI_API_KEY='')
    def test_requires_an_api_key(self):
        with self.assertRaisesMessage(CommandError, 'OPENAI_API_KEY'):
            self.draft_article()


class AdminTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser('admin'))
        self.post = create_post('Admin post', category=create_category())

    def test_post_and_category_pages_load(self):
        urls = [
            reverse('admin:blog_post_changelist'),
            reverse('admin:blog_post_add'),
            reverse('admin:blog_post_change', args=[self.post.pk]),
            reverse('admin:blog_category_changelist'),
            reverse('admin:blog_category_change', args=[self.post.category.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
