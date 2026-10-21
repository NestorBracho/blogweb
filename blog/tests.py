import base64
import json
import logging
import time
from datetime import datetime
from io import BytesIO, StringIO
from tempfile import TemporaryDirectory
from unittest import mock
from urllib.parse import quote

import httpx2
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import CommandError, call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.urls import reverse, reverse_lazy
from openai import OpenAI
from PIL import Image
from rest_framework.throttling import SimpleRateThrottle

from config.testing import EmptyCacheMixin, create_category, create_post, reverse_in, structured_data
from config.throttling import AnonRateThrottle, WriteRateThrottle

from . import covers
from .drafting import ArticleDraft
from .models import Category, Post
from .rendering import render_markdown


def image_file(name='cover.png', size=(2400, 1600), mode='RGB', color='teal'):
    output = BytesIO()
    Image.new(mode, size, color).save(output, 'PNG')
    return SimpleUploadedFile(name, output.getvalue(), content_type='image/png')


def stored_image(path):
    with default_storage.open(path) as file, Image.open(file) as image:
        return image.format, image.size


class TemporaryMediaMixin:
    """Uploaded and generated files go to a folder of their own, deleted after each test."""

    def setUp(self):
        super().setUp()
        media_root = TemporaryDirectory()
        self.addCleanup(media_root.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media_root.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)


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

    def test_post_without_cover_shows_no_image(self):
        response = self.get(self.post)

        self.assertNotContains(response, 'class="post-image"')

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

    def test_link_previews_know_it_is_an_article(self):
        response = self.get(self.post)

        self.assertContains(response, '<meta property="og:type" content="article">')
        published, modified = self.post.created.isoformat(), self.post.updated.isoformat()
        self.assertContains(response, f'<meta property="article:published_time" content="{published}">')
        self.assertContains(response, f'<meta property="article:modified_time" content="{modified}">')

    def test_search_engines_get_the_post_as_structured_data(self):
        post = create_post('Black holes', title_es='Agujeros negros', description_es='Sobre agujeros negros')

        data = structured_data(self.client.get(reverse_in('es', 'blog:post-detail', slug=post.slug)))

        self.assertEqual((data['@type'], data['headline']), ('BlogPosting', 'Agujeros negros'))
        self.assertEqual((data['description'], data['inLanguage']), ('Sobre agujeros negros', 'es'))
        self.assertEqual(data['url'], f'http://testserver{reverse_in("es", "blog:post-detail", slug=post.slug)}')
        self.assertEqual(data['datePublished'], post.created.isoformat())
        self.assertEqual(data['author']['name'], 'Nestor Bracho')

    def test_structured_data_cannot_close_its_script_element(self):
        title = '</script><script>alert(1)</script>'
        post = create_post(title)

        response = self.get(post)

        self.assertNotContains(response, '</script><script>alert(1)')
        self.assertEqual(structured_data(response)['headline'], title)

    def test_body_is_rendered_from_markdown(self):
        body = 'Some **bold** text\n\n<script>alert("hi")</script>'
        post = create_post('Markdown', body_es=body, body_en=body)

        response = self.get(post)

        self.assertContains(response, '<p>Some <strong>bold</strong> text</p>', html=True)
        self.assertNotContains(response, 'alert("hi")')


class CategoryDetailViewTests(TestCase):
    def test_title_and_description_name_the_category(self):
        category = create_category('rust', name_en='Rust', name_es='Rust')
        create_post('Ownership', category=category)

        response = self.client.get(reverse_in('en', 'blog:category-detail', slug=category.slug))

        self.assertContains(response, '<title>Rust - Nestor Bracho</title>')
        self.assertContains(response, '<meta name="description" content="Posts about Rust by Nestor Bracho.">')

    def test_post_count_agrees_in_number(self):
        one = create_category('one-post')
        create_post('Only', category=one)
        two = create_category('two-posts')
        create_post('First', category=two)
        create_post('Second', category=two)

        def get(category, language):
            return self.client.get(reverse_in(language, 'blog:category-detail', slug=category.slug))

        self.assertContains(get(one, 'en'), 'A collection of <span>1 post</span>')
        self.assertContains(get(two, 'en'), 'A collection of <span>2 posts</span>')
        self.assertContains(get(one, 'es'), 'Una colección de <span>1 publicación</span>')
        self.assertContains(get(two, 'es'), 'Una colección de <span>2 publicaciones</span>')

    def test_long_categories_are_paginated(self):
        category = create_category()
        for number in range(13):
            create_post(f'Post {number}', days_ago=number, category=category)

        first = self.client.get(category.get_absolute_url())
        second = self.client.get(category.get_absolute_url(), {'page': 2})

        self.assertEqual(len(first.context['post_list']), 12)
        self.assertContains(first, '13 ')
        self.assertContains(first, 'href="?page=2" rel="next"')
        self.assertEqual([post.title_en for post in second.context['post_list']], ['Post 12'])
        # Each page of the list is a page of its own for search engines
        second_page = f'http://testserver{category.get_absolute_url()}?page=2'
        self.assertContains(second, f'<link rel="canonical" href="{second_page}">')

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

    def test_categories_without_published_posts_are_not_found_yet(self):
        empty = create_category('empty-topic')
        drafts_only = create_category('drafts-only')
        create_post('Draft', category=drafts_only, is_published=False)

        for category in (empty, drafts_only):
            with self.subTest(category=category.slug):
                self.assertEqual(self.client.get(category.get_absolute_url()).status_code, 404)

    def test_a_category_appears_with_its_first_published_post(self):
        category = create_category('future-topic')
        post = create_post('Coming soon', category=category, is_published=False)

        Post.objects.filter(pk=post.pk).update(is_published=True)

        self.assertEqual(self.client.get(category.get_absolute_url()).status_code, 200)


class SidebarTests(TestCase):
    def test_lists_only_categories_with_published_posts(self):
        published = create_category('published-topic')
        create_post('Published', category=published)
        create_post('Draft', category=create_category('drafts-only'), is_published=False)
        create_category('empty-topic')

        response = self.client.get(reverse('main:index'))

        # The data migrations' categories have no posts here, so only one is left
        self.assertEqual(list(response.context['categories']), [published])

    def test_sidebar_and_footer_share_the_latest_posts(self):
        # More than the home's first page shows, or the sidebar leaves them out
        for number in range(5):
            create_post(f'Post {number}', days_ago=number)
        create_post('Draft', is_published=False)

        # A page that lists no other posts
        response = self.client.get(reverse_in('en', 'main:about'))

        latest = [post.title_en for post in response.context['latest_posts']]
        self.assertEqual(latest, ['Post 0', 'Post 1', 'Post 2'])
        # Same posts in both lists
        self.assertContains(response, f'href="{reverse_in("en", "blog:post-detail", slug="post-0")}"', count=4)


class CategoryDeletionTests(TestCase):
    def test_deleting_a_category_keeps_its_posts(self):
        category = create_category()
        post = create_post('Post', category=category)

        category.delete()

        post.refresh_from_db()
        self.assertIsNone(post.category)


class CategoryParentTests(TestCase):
    def test_deleting_a_category_keeps_the_ones_inside_it(self):
        science = create_category('science-topic')
        physics = create_category('physics-topic', parent=science)

        science.delete()

        physics.refresh_from_db()
        self.assertIsNone(physics.parent)

    def test_a_category_cannot_be_inside_itself(self):
        science = create_category('science-topic')
        physics = create_category('physics-topic', parent=science)

        for parent in [science, physics]:
            with self.subTest(parent=parent.slug):
                science.parent = parent
                with self.assertRaises(ValidationError) as error:
                    science.full_clean()
                self.assertEqual(list(error.exception.message_dict), ['parent'])

    def test_a_loop_saved_some_other_way_does_not_hang_validation(self):
        first = create_category('first-topic')
        second = create_category('second-topic', parent=first)
        Category.objects.filter(pk=first.pk).update(parent=second)
        create_category('third-topic', parent=first)

        with self.assertRaises(ValidationError):
            Category.objects.get(slug='third-topic').full_clean()


class FeedTests(TestCase):
    def test_feed_lists_published_posts_only(self):
        create_post('Published post')
        create_post('Draft post', is_published=False)

        response = self.client.get(reverse('blog:feed'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('application/rss+xml', response['Content-Type'])
        self.assertContains(response, 'Published post')
        self.assertNotContains(response, 'Draft post')

    def test_each_language_has_its_own_feed(self):
        post = create_post('Black holes', title_es='Agujeros negros')

        for language, title in [('en', 'Black holes'), ('es', 'Agujeros negros')]:
            with self.subTest(language=language):
                feed_url = reverse_in(language, 'blog:feed')
                response = self.client.get(feed_url)
                page = self.client.get(reverse_in(language, 'main:index'))

                post_url = f'http://testserver{reverse_in(language, "blog:post-detail", slug=post.slug)}'
                self.assertContains(response, f'<language>{language}</language>')
                self.assertContains(response, f'<title>{title}</title><link>{post_url}</link>')
                self.assertContains(page, f'type="application/rss+xml" title="Nestor Bracho" href="{feed_url}"')


class SitemapTests(TestCase):
    def test_sitemap_lists_pages_and_published_content(self):
        published = create_post('Published', category=create_category('other-topic'))
        draft = create_post('Draft', is_published=False, category=create_category('drafts-only'))

        response = self.client.get(reverse('sitemap'))

        self.assertEqual(response.status_code, 200)
        for language in ['en', 'es']:
            with self.subTest(language=language):
                pages = [
                    reverse_in(language, 'main:about'),
                    reverse_in(language, 'blog:post-detail', slug=published.slug),
                    reverse_in(language, 'blog:category-detail', slug=published.category.slug),
                ]
                for page in pages:
                    self.assertContains(response, f'<loc>http://testserver{page}</loc>')
        self.assertNotContains(response, f'/post/{draft.slug}')
        self.assertNotContains(response, f'/tags/{draft.category.slug}')

    def test_sitemap_links_each_page_to_its_other_language(self):
        response = self.client.get(reverse('sitemap'))

        for language in ['en', 'es']:
            cv = f'http://testserver{reverse_in(language, "main:cv")}'
            self.assertContains(response, f'<xhtml:link rel="alternate" hreflang="{language}" href="{cv}"/>')
        # For everyone else, the address without a language, which redirects to theirs
        self.assertContains(response, '<xhtml:link rel="alternate" hreflang="x-default" href="http://testserver/cv/"/>')


class PostAPITests(EmptyCacheMixin, TestCase):
    url = reverse_lazy('api:post-list')

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

        self.assertEqual([post['title'] for post in spanish.json()['results']], ['Agujeros negros'])
        self.assertEqual(english.json()['results'], [])

    def test_search_needs_every_word_somewhere_in_the_post(self):
        create_post('Ownership in Rust', body_en='How the borrow checker frees memory.')

        found = self.client.get(self.url, {'search': 'rust memory'}, headers={'X-Language': 'en'})
        missing = self.client.get(self.url, {'search': 'rust python'}, headers={'X-Language': 'en'})

        self.assertEqual(found.json()['count'], 1)
        self.assertEqual(missing.json()['count'], 0)

    def test_page_size_can_be_raised_up_to_a_limit(self):
        for number in range(25):
            create_post(f'Post {number}')

        bigger = self.client.get(self.url, {'page_size': 10})
        capped = self.client.get(self.url, {'page_size': 100})

        self.assertEqual(len(bigger.json()['results']), 10)
        self.assertEqual(len(capped.json()['results']), 20)

    def test_language_header_applies_to_the_whole_response(self):
        category = create_category(name_en='Space', name_es='Espacio')
        post = create_post('Black holes', title_es='Agujeros negros', category=category)

        # The page sends the language it is in, whatever the browser prefers
        response = self.client.get(self.url, headers={'X-Language': 'es', 'Accept-Language': 'en'})

        result = response.json()['results'][0]
        self.assertEqual((result['title'], result['category']['name']), ('Agujeros negros', 'Espacio'))
        self.assertEqual(result['url'], reverse_in('es', 'blog:post-detail', slug=post.slug))
        self.assertEqual(result['category']['url'], reverse_in('es', 'blog:category-detail', slug=category.slug))
        self.assertIn('X-Language', response['Vary'])

    def test_language_follows_the_browser_without_the_header(self):
        create_post('Black holes', title_es='Agujeros negros')

        spanish = self.client.get(self.url, headers={'Accept-Language': 'es'})
        default = self.client.get(self.url)

        self.assertEqual(spanish.json()['results'][0]['title'], 'Agujeros negros')
        self.assertEqual(default.json()['results'][0]['title'], 'Black holes')

    def test_posts_are_raw_data_for_clients_to_format(self):
        post = create_post('Black holes', body_en='word ' * 450, category=create_category(color='#4643ec'))

        result = self.client.get(self.url).json()['results'][0]

        self.assertEqual(
            set(result),
            {'id', 'slug', 'url', 'title', 'description', 'category', 'cover_urls', 'read_time', 'created', 'updated'},
        )
        self.assertEqual(result['id'], str(post.pk))
        # Minutes as a number and dates as ISO 8601, with no wording in any language
        self.assertEqual(result['read_time'], 3)
        self.assertEqual(datetime.fromisoformat(result['created']), post.created)
        self.assertEqual(datetime.fromisoformat(result['updated']), post.updated)
        self.assertEqual(
            result['category'],
            {'slug': 'test-topic', 'name': 'test-topic', 'color': '#4643ec', 'url': '/en/tags/test-topic'},
        )

    def test_posts_without_a_category_say_so(self):
        create_post('Uncategorized', category=None)

        self.assertIsNone(self.client.get(self.url).json()['results'][0]['category'])

    def test_a_single_post_comes_whole(self):
        post = create_post('Black holes', body_en='Light *cannot* escape.', body_es='La luz no escapa.')

        response = self.client.get(reverse('api:post-detail', args=[post.pk]), headers={'X-Language': 'en'})

        result = response.json()
        self.assertEqual(result['title'], 'Black holes')
        # The Markdown it is written in, in the language asked for
        self.assertEqual(result['body'], 'Light *cannot* escape.')
        self.assertIs(result['is_published'], True)

    def test_anonymous_users_cannot_create_posts(self):
        response = self.client.post(self.url, {'title_en': 'Spam'})

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Post.objects.filter(title_en='Spam').exists())

    def test_staff_passwords_sign_nobody_in(self):
        # Only the admin's session does: the API is no place to try passwords
        get_user_model().objects.create_user(username='editor', password='correct horse', is_staff=True)
        draft = create_post('Draft', is_published=False)
        credentials = base64.b64encode(b'editor:correct horse').decode()
        headers = {'Authorization': f'Basic {credentials}'}

        created = self.client.post(self.url, {'title_en': 'Spam'}, headers=headers)
        read = self.client.get(reverse('api:post-detail', args=[draft.pk]), headers=headers)

        self.assertEqual(created.status_code, 403)
        self.assertFalse(Post.objects.filter(title_en='Spam').exists())
        self.assertEqual(read.status_code, 404)

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
        self.assertEqual((response.json()['slug'], response.json()['is_published']), ('hello-world', False))
        self.assertEqual(response.json()['id'], str(Post.objects.get(slug='hello-world').pk))

    def test_staff_can_edit_and_publish_a_draft(self):
        self.client.force_login(get_user_model().objects.create_user(username='editor', is_staff=True))
        draft = create_post('Draft', is_published=False)
        detail_url = reverse('api:post-detail', args=[draft.pk])
        self.assertIs(self.client.get(detail_url).json()['is_published'], False)

        response = self.client.patch(
            detail_url, {'title_en': 'Ready', 'is_published': True}, content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        draft.refresh_from_db()
        self.assertEqual((draft.title_en, draft.is_published), ('Ready', True))
        # Publishing doesn't move the post to a new URL
        self.assertEqual(draft.slug, 'draft')

    def test_staff_can_delete_a_draft(self):
        self.client.force_login(get_user_model().objects.create_user(username='editor', is_staff=True))
        draft = create_post('Draft', is_published=False)

        response = self.client.delete(reverse('api:post-detail', args=[draft.pk]))

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Post.objects.filter(pk=draft.pk).exists())

    def test_the_list_never_shows_drafts_even_to_staff(self):
        # The home page reads this list, and the site owner browses it signed in to the admin
        self.client.force_login(get_user_model().objects.create_user(username='editor', is_staff=True))
        create_post('Published')
        create_post('Draft', is_published=False)

        response = self.client.get(self.url)

        self.assertEqual([post['title'] for post in response.json()['results']], ['Published'])

    def test_anonymous_users_cannot_see_or_change_drafts(self):
        draft = create_post('Draft', is_published=False)
        detail_url = reverse('api:post-detail', args=[draft.pk])

        self.assertEqual(self.client.get(detail_url).status_code, 404)
        response = self.client.patch(detail_url, {'is_published': True}, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        draft.refresh_from_db()
        self.assertFalse(draft.is_published)


class APIRateLimitTests(EmptyCacheMixin, TestCase):
    url = reverse_lazy('api:post-list')

    def test_visitors_get_a_number_of_reads_a_minute(self):
        for _ in range(AnonRateThrottle().num_requests):
            self.assertEqual(self.client.get(self.url).status_code, 200)

        too_many = self.client.get(self.url)
        a_minute_later = time.time() + 60
        with mock.patch.object(SimpleRateThrottle, 'timer', return_value=a_minute_later):
            next_minute = self.client.get(self.url)

        self.assertEqual(too_many.status_code, 429)
        self.assertIn('Retry-After', too_many)
        self.assertEqual(next_minute.status_code, 200)

    def test_counts_each_visitor_by_the_address_cloudflare_gives(self):
        visitor = {'CF-Connecting-IP': '203.0.113.7'}
        for _ in range(AnonRateThrottle().num_requests):
            self.client.get(self.url, headers=visitor)

        # Anyone can make up X-Forwarded-For addresses, so they don't make a new visitor
        spoofed = self.client.get(self.url, headers={**visitor, 'X-Forwarded-For': '198.51.100.1'})
        someone_else = self.client.get(self.url, headers={'CF-Connecting-IP': '203.0.113.8'})

        self.assertEqual(spoofed.status_code, 429)
        self.assertEqual(someone_else.status_code, 200)

    def test_staff_get_fewer_writes_than_reads(self):
        self.client.force_login(get_user_model().objects.create_user(username='editor', is_staff=True))
        detail_url = reverse('api:post-detail', args=[create_post('Post').pk])
        for _ in range(WriteRateThrottle().num_requests):
            self.client.patch(detail_url, {'title_en': 'Edited'}, content_type='application/json')

        write = self.client.patch(detail_url, {'title_en': 'One too many'}, content_type='application/json')
        read = self.client.get(detail_url)

        self.assertEqual(write.status_code, 429)
        self.assertEqual(read.status_code, 200)
        self.assertEqual(read.json()['title'], 'Edited')


class RenderMarkdownTests(SimpleTestCase):
    def test_keeps_highlighted_code_admonitions_classes_and_aligned_tables(self):
        html = render_markdown(
            '```python\ndef f():\n    pass\n```\n\n'
            '!!! note\n    Careful.\n\n'
            'A remark\n{: .note }\n\n'
            '| Name | Total |\n|:-----|------:|\n| a    | 1     |\n'
        )

        self.assertIn('<div class="highlight"><pre><span></span><code><span class="k">def</span>', html)
        self.assertIn('<div class="admonition note">', html)
        self.assertIn('<p class="note">A remark</p>', html)
        self.assertIn('<td style="text-align:right">1</td>', html)

    def test_removes_scripts(self):
        html = render_markdown('Hello\n\n<script>alert("hi")</script>')

        self.assertHTMLEqual(html, '<p>Hello</p>')

    def test_removes_event_handlers_from_raw_html_and_attribute_lists(self):
        html = render_markdown('<img src="/media/a.jpg" onerror="alert(1)">\n\nA paragraph\n{: onclick="alert(1)" }')

        self.assertHTMLEqual(html, '<p><img src="/media/a.jpg"></p><p>A paragraph</p>')

    def test_keeps_links_but_not_script_urls(self):
        html = render_markdown('[safe](https://example.com) and [unsafe](javascript:alert(1))')

        self.assertHTMLEqual(
            html,
            '<p><a href="https://example.com" rel="noopener noreferrer">safe</a> and '
            '<a rel="noopener noreferrer">unsafe</a></p>',
        )

    def test_removes_embedded_frames_and_inline_styles(self):
        html = render_markdown('<iframe src="https://example.com"></iframe>\n\n<p style="position: fixed">Text</p>')

        self.assertHTMLEqual(html, '<p>Text</p>')


class CoverSizesTests(TemporaryMediaMixin, TestCase):
    def test_a_new_cover_is_made_at_the_size_of_each_place(self):
        post = create_post('Covered', cover=image_file())

        paths = post.cover_sizes['paths']
        self.assertEqual(post.cover_sizes['source'], post.cover.name)
        # Twice the largest box each place shows (4:3), and the size link previews use
        self.assertEqual(stored_image(paths['post']), ('WEBP', (1712, 1284)))
        self.assertEqual(stored_image(paths['card']), ('WEBP', (824, 618)))
        self.assertEqual(stored_image(paths['thumb']), ('WEBP', (180, 136)))
        self.assertEqual(stored_image(paths['social']), ('JPEG', (1200, 630)))

    def test_small_covers_are_cropped_to_shape_but_never_enlarged(self):
        post = create_post('Small', cover=image_file(size=(1024, 1024)))

        self.assertEqual(stored_image(post.cover_sizes['paths']['post'])[1], (1024, 768))
        self.assertEqual(stored_image(post.cover_sizes['paths']['social'])[1], (1024, 538))

    def test_transparent_covers_are_put_on_white(self):
        post = create_post('Transparent', cover=image_file(mode='RGBA', color=(0, 0, 0, 0)))

        with default_storage.open(post.cover_sizes['paths']['social']) as file, Image.open(file) as image:
            self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))

    def test_pages_show_the_size_each_place_needs(self):
        post = create_post('Covered', cover=image_file(), category=create_category())
        # Enough older posts for the sidebar to list the latest ones
        for number in range(4):
            create_post(f'Older {number}', days_ago=number + 1)

        post_page = self.client.get(post.get_absolute_url())
        category_page = self.client.get(post.category.get_absolute_url())
        home = self.client.get(reverse('main:index'))

        urls = post.cover_urls
        self.assertContains(post_page, f'src="{urls["post"]}"')
        self.assertContains(post_page, f'<meta property="og:image" content="http://testserver{urls["social"]}">')
        self.assertContains(post_page, f'src="{urls["thumb"]}"')  # the sidebar's latest posts
        self.assertContains(category_page, f'<img src="{urls["card"]}"')
        self.assertContains(home, f'<img src="{urls["card"]}"')

    def test_the_post_page_gives_the_size_of_its_cover_and_loads_it_first(self):
        post = create_post('Covered', cover=image_file())

        response = self.client.get(post.get_absolute_url())

        width, height = (2 * side for side in covers.SIZES['post'])
        self.assertContains(
            response, f'src="{post.cover_urls["post"]}" width="{width}" height="{height}" fetchpriority="high"'
        )

    def test_phones_get_the_cover_at_the_card_size(self):
        post = create_post('Covered', cover=image_file())

        response = self.client.get(post.get_absolute_url())

        card_width, post_width = 2 * covers.SIZES['card'][0], 2 * covers.SIZES['post'][0]
        urls = post.cover_urls
        self.assertContains(response, f'srcset="{urls["card"]} {card_width}w, {urls["post"]} {post_width}w"')

    def test_the_api_gives_every_size(self):
        post = create_post('Covered', cover=image_file())

        response = self.client.get(reverse('api:post-list'))

        self.assertEqual(response.json()['results'][0]['cover_urls'], post.cover_urls)

    def test_a_new_cover_replaces_the_sizes_of_the_old_one(self):
        post = create_post('Covered', cover=image_file())
        old_paths = post.cover_sizes['paths'].values()

        post.cover = image_file('other.png', color='orange')
        post.save()

        self.assertFalse(any(default_storage.exists(path) for path in old_paths))
        self.assertTrue(all(default_storage.exists(path) for path in post.cover_sizes['paths'].values()))

    def test_removing_the_cover_removes_its_sizes(self):
        post = create_post('Covered', cover=image_file())
        old_paths = post.cover_sizes['paths'].values()

        post.cover = None
        post.save()

        self.assertEqual(post.cover_sizes, {})
        self.assertFalse(any(default_storage.exists(path) for path in old_paths))
        self.assertEqual(set(post.cover_urls.values()), {''})

    def test_saving_without_changing_the_cover_makes_nothing_again(self):
        post = create_post('Covered', cover=image_file())

        with mock.patch('blog.covers.make_sizes') as make_sizes:
            post.title_en = 'Still covered'
            post.save()

        make_sizes.assert_not_called()

    def test_an_unreadable_cover_falls_back_to_the_original(self):
        with self.assertLogs('blog.models', 'ERROR'):
            post = create_post('Broken', cover=SimpleUploadedFile('broken.png', b'not an image'))

        self.assertEqual(post.cover_sizes, {})
        self.assertEqual(set(post.cover_urls.values()), {post.cover.url})

    def test_the_command_makes_the_sizes_of_older_covers(self):
        post = create_post('Older', cover=image_file())
        paths = post.cover_sizes['paths']
        # As a cover saved before sizes existed: no sizes recorded, no files
        Post.objects.filter(pk=post.pk).update(cover_sizes={})
        for path in paths.values():
            default_storage.delete(path)

        output = StringIO()
        call_command('make_cover_sizes', stdout=output)

        post.refresh_from_db()
        self.assertEqual(post.cover_sizes['paths'], paths)
        self.assertTrue(all(default_storage.exists(path) for path in paths.values()))
        self.assertIn('older: post, card, thumb, social', output.getvalue())

    def test_the_command_does_not_make_existing_sizes_again(self):
        create_post('Covered', cover=image_file())

        with mock.patch.object(default_storage, 'save') as save:
            call_command('make_cover_sizes', stdout=StringIO())

        save.assert_not_called()


class ReadTimeTests(TestCase):
    def test_is_worked_out_from_the_text(self):
        post = create_post('Long read', body_en='word ' * 450, body_es='palabra ' * 300)

        # 450 words at 200 per minute, rounded up; the longer language wins
        self.assertEqual(post.read_time, 3)

    def test_is_at_least_a_minute(self):
        self.assertEqual(create_post('Short').read_time, 1)

    def test_follows_edits(self):
        post = create_post('Growing')

        post.body_en = 'word ' * 1000
        post.save()

        self.assertEqual(post.read_time, 5)

    def test_cannot_be_set_by_hand(self):
        post = create_post('Short', read_time=30)

        self.assertEqual(post.read_time, 1)


class MigrationTestCase(TransactionTestCase):
    """Makes data with the models as they were before a migration (`before`) and reads it after (`after`)."""

    def setUp(self):
        super().setUp()
        # The next test finds the database fully migrated, whichever migration this one stopped at
        self.addCleanup(self.migrate_to_latest)

    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def migrate_to_latest(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())


class ReadTimeMigrationTests(MigrationTestCase):
    before = [('blog', '0004_post_category_set_null')]
    after = [('blog', '0005_post_read_time_from_text')]

    def test_works_out_the_read_time_of_existing_posts(self):
        old_post = self.migrate(self.before).get_model('blog', 'Post')
        old_post.objects.create(
            slug='typed-by-hand',
            title_en='Typed by hand',
            title_es='A mano',
            body_en='word ' * 450,
            body_es='palabra',
            description_en='Description',
            description_es='Descripción',
            read_time=7,
        )

        new_post = self.migrate(self.after).get_model('blog', 'Post')

        self.assertEqual(new_post.objects.get(slug='typed-by-hand').read_time, 3)


class CategoryParentMigrationTests(MigrationTestCase):
    before = [('blog', '0006_post_cover_sizes')]
    after = [('blog', '0007_category_parent')]

    def test_keeps_each_category_inside_the_same_one(self):
        old_category = self.migrate(self.before).get_model('blog', 'Category')
        science = old_category.objects.create(name_en='Science', name_es='Ciencia', slug='science-old', color='#000')
        old_category.objects.create(
            name_en='Physics', name_es='Física', slug='physics-old', color='#000', sub_category=science
        )

        new_category = self.migrate(self.after).get_model('blog', 'Category')

        physics = new_category.objects.get(slug='physics-old')
        self.assertEqual(physics.parent_id, science.pk)
        self.assertEqual(list(physics.parent.children.all()), [physics])

    def test_leaves_the_table_as_it_is(self):
        # So the code still running during a deploy, which knows the old field, keeps working
        for backwards in [False, True]:
            with self.subTest(backwards=backwards):
                sql = StringIO()
                call_command('sqlmigrate', 'blog', '0007_category_parent', backwards=backwards, stdout=sql)
                self.assertNotIn('TABLE', sql.getvalue())


class PostSlugTests(TestCase):
    def test_slug_comes_from_the_english_title(self):
        post = Post.objects.create(
            title_es='Hola mundo',
            title_en='Hello world',
            body_es='Cuerpo',
            body_en='Body',
            description_es='Descripción',
            description_en='Description',
        )

        self.assertEqual(post.slug, 'hello-world')

    def test_slug_falls_back_to_the_spanish_title(self):
        post = Post.objects.create(
            title_es='Hola mundo', body_es='Cuerpo', body_en='', description_es='Descripción', description_en=''
        )

        self.assertEqual(post.slug, 'hola-mundo')

    def test_slugs_stay_unique(self):
        first = create_post('Same title')
        second = create_post('Same title')

        self.assertEqual((first.slug, second.slug), ('same-title', 'same-title-1'))


class PublishedPostsTests(TestCase):
    def test_leave_out_drafts(self):
        category = create_category()
        published = create_post('Published', category=category)
        create_post('Draft', category=category, is_published=False)

        self.assertEqual(list(Post.objects.published()), [published])
        self.assertEqual(list(category.posts.published()), [published])

    def test_date_each_category_by_its_newest_published_post(self):
        older = create_category('older-topic')
        create_post('Old', days_ago=5, category=older)
        create_post('Draft written today', category=older, is_published=False)
        newer = create_category('newer-topic')
        recent = create_post('Recent', days_ago=1, category=newer)

        categories = list(Category.objects.with_published_posts().order_by('-latest_post'))

        self.assertEqual(categories, [newer, older])
        self.assertEqual(categories[0].latest_post, recent.created)


class CategoryAPITests(EmptyCacheMixin, TestCase):
    def test_lists_categories_with_their_latest_published_posts(self):
        category = create_category()
        old = create_post('Old', days_ago=2, category=category)
        create_post('New', days_ago=1, category=category)
        create_post('Draft', category=category, is_published=False)
        create_category('empty-topic')
        create_post('Only a draft', category=create_category('drafts-only'), is_published=False)
        # Newest first by date of publication, as everywhere else, however recently a post was edited
        old.save()

        response = self.client.get(reverse('api:categories'))

        categories = response.json()['results']
        self.assertEqual([category['slug'] for category in categories], ['test-topic'])
        self.assertEqual(set(categories[0]), {'slug', 'name', 'color', 'url', 'latest_posts'})
        self.assertEqual([post['title'] for post in categories[0]['latest_posts']], ['New', 'Old'])

    def test_shows_the_four_most_active_categories_and_five_posts_of_each(self):
        for number in range(5):
            category = create_category(f'topic-{number}')
            for days_ago in range(6):
                create_post(f'Topic {number} post {days_ago}', days_ago=10 * number + days_ago, category=category)

        categories = self.client.get(reverse('api:categories')).json()['results']

        self.assertEqual([category['slug'] for category in categories], [f'topic-{number}' for number in range(4)])
        self.assertEqual([len(category['latest_posts']) for category in categories], [5, 5, 5, 5])

    def test_the_address_ends_in_a_slash_like_the_others(self):
        self.assertEqual(reverse('api:categories'), '/api/categories/')
        self.assertEqual(reverse('api:post-list'), '/api/post/')
        # The old address still works
        self.assertRedirects(self.client.get('/api/categories'), '/api/categories/', status_code=301)


def article_reply(*content):
    """A Responses API reply with one message made of these parts, as the API sends it."""
    message = {'type': 'message', 'id': 'msg_test', 'role': 'assistant', 'status': 'completed', 'content': content}
    return {
        'id': 'resp_test',
        'object': 'response',
        'created_at': 0,
        'model': 'test-model',
        'status': 'completed',
        'output': [message],
        'parallel_tool_calls': True,
        'tool_choice': 'auto',
        'tools': [],
    }


def output_text(text):
    return {'type': 'output_text', 'text': text, 'annotations': []}


@override_settings(OPENAI_API_KEY='test-key', OPENAI_MODEL='test-model', OPENAI_IMAGE_MODEL='test-image-model')
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
        # No request ever leaves the test: the command gets a real client whose requests are answered by fake_api(),
        # so the SDK still builds them and parses the replies as it does with the real API
        cover = base64.b64encode(image_file(size=(1536, 1024)).read()).decode()
        self.replies = {
            '/v1/responses': article_reply(output_text(self.draft.model_dump_json())),
            '/v1/images/generations': {'created': 0, 'data': [{'b64_json': cover}]},
        }
        self.requests = {}
        client = OpenAI(
            api_key='test-key',
            base_url='https://api.openai.test/v1',
            max_retries=0,
            http_client=httpx2.Client(transport=httpx2.MockTransport(self.fake_api)),
        )
        self.addCleanup(client.close)
        patcher = mock.patch('blog.management.commands.draft_article.OpenAI', return_value=client)
        patcher.start()
        self.addCleanup(patcher.stop)
        # httpx2 logs every request at INFO, and the root logger would print those lines among the test results
        http_logger = logging.getLogger('httpx2')
        self.addCleanup(http_logger.setLevel, http_logger.level)
        http_logger.setLevel(logging.WARNING)

    def fake_api(self, request):
        self.requests[request.url.path] = json.loads(request.content)
        reply = self.replies[request.url.path]
        return reply if isinstance(reply, httpx2.Response) else httpx2.Response(200, json=reply)

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
        self.assertNotIn('/v1/images/generations', self.requests)

    def test_asks_for_structured_output(self):
        self.draft_article('--no-cover')

        request = self.requests['/v1/responses']
        self.assertEqual(request['model'], 'test-model')
        self.assertIn('Rust ownership', request['input'])
        # The SDK turns ArticleDraft into a strict JSON schema, so the model has to fill in every field
        schema = request['text']['format']
        self.assertEqual((schema['type'], schema['name'], schema['strict']), ('json_schema', 'ArticleDraft', True))
        self.assertEqual(schema['schema']['required'], list(ArticleDraft.model_fields))
        self.assertIs(request['store'], False)

    def test_shortens_texts_that_do_not_fit_their_columns(self):
        too_long = self.draft.model_copy(update={'title_en': 'A' * 80, 'description_es': 'B' * 200})
        self.replies['/v1/responses'] = article_reply(output_text(too_long.model_dump_json()))

        self.draft_article('--no-cover')

        post = Post.objects.get(category=self.category)
        self.assertEqual(len(post.title_en), 60)
        self.assertEqual(len(post.description_es), 160)

    def test_attaches_a_generated_cover_at_every_size(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.draft_article()

            post = Post.objects.get(slug='ownership-in-rust')
            self.assertEqual(stored_image(post.cover.name), ('PNG', (1536, 1024)))
            self.assertEqual(list(post.cover_sizes['paths']), ['post', 'card', 'thumb', 'social'])
        request = self.requests['/v1/images/generations']
        self.assertEqual(request['model'], 'test-image-model')
        self.assertIn('Ownership in Rust', request['prompt'])

    def test_keeps_the_draft_when_the_cover_fails(self):
        self.replies['/v1/images/generations'] = httpx2.Response(503, json={'error': {'message': 'Unavailable'}})

        output = self.draft_article()

        self.assertFalse(Post.objects.get(slug='ownership-in-rust').cover)
        self.assertIn('without a cover', output)

    def test_keeps_the_draft_when_no_image_comes_back(self):
        self.replies['/v1/images/generations'] = {'created': 0, 'data': []}

        output = self.draft_article()

        self.assertFalse(Post.objects.get(slug='ownership-in-rust').cover)
        self.assertIn('without a cover: the model returned no image', output)

    def test_reports_a_refusal_without_saving_anything(self):
        self.replies['/v1/responses'] = article_reply({'type': 'refusal', 'refusal': 'I cannot write that.'})

        with self.assertRaisesMessage(CommandError, 'I cannot write that.'):
            self.draft_article()

        self.assertFalse(Post.objects.filter(category=self.category).exists())

    def test_reports_an_article_that_was_cut_short(self):
        self.replies['/v1/responses'] = article_reply(output_text(self.draft.model_dump_json()[:200]))

        with self.assertRaisesMessage(CommandError, 'the model returned an incomplete article'):
            self.draft_article()

        self.assertFalse(Post.objects.filter(category=self.category).exists())

    def test_reports_an_answer_without_an_article(self):
        self.replies['/v1/responses'] = article_reply()

        with self.assertRaisesMessage(CommandError, 'the model returned no article'):
            self.draft_article()

        self.assertFalse(Post.objects.filter(category=self.category).exists())

    def test_reports_api_errors_without_saving_anything(self):
        self.replies['/v1/responses'] = httpx2.Response(401, json={'error': {'message': 'Incorrect API key'}})

        with self.assertRaisesMessage(CommandError, 'Incorrect API key'):
            self.draft_article()

        self.assertFalse(Post.objects.filter(category=self.category).exists())

    def test_rejects_an_unknown_category(self):
        with self.assertRaisesMessage(CommandError, 'Unknown category "missing"'):
            call_command('draft_article', 'Rust ownership', '--category', 'missing')

        self.assertEqual(self.requests, {})

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

    def test_categories_show_the_one_they_are_inside(self):
        create_category('child-topic', parent=self.post.category)

        response = self.client.get(reverse('admin:blog_category_changelist'))

        self.assertContains(response, '<td class="field-parent nowrap">test-topic</td>', html=True)
