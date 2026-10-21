import base64
from io import BytesIO, StringIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock
from urllib.parse import quote

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import CommandError, call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.urls import reverse, reverse_lazy
from openai import OpenAIError
from PIL import Image

from config.testing import create_category, create_post, reverse_in, structured_data

from .drafting import ArticleDraft
from .models import Post
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
        for number in range(4):
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


class PostAPITests(TestCase):
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
        post = create_post('Black holes', title_es='Agujeros negros', body_en='word ' * 450)

        # The page sends the language it is in, whatever the browser prefers
        response = self.client.get(self.url, headers={'X-Language': 'es', 'Accept-Language': 'en'})

        result = response.json()['results'][0]
        self.assertEqual((result['title'], result['read_time']), ('Agujeros negros', '3 min de lectura'))
        self.assertEqual(result['href'], reverse_in('es', 'blog:post-detail', slug=post.slug))
        self.assertIn('X-Language', response['Vary'])

    def test_language_follows_the_browser_without_the_header(self):
        create_post('Black holes', title_es='Agujeros negros', body_en='word ' * 450)

        spanish = self.client.get(self.url, headers={'Accept-Language': 'es'})
        default = self.client.get(self.url)

        self.assertEqual(spanish.json()['results'][0]['read_time'], '3 min de lectura')
        self.assertEqual(default.json()['results'][0]['read_time'], '3 min read')

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
        self.assertEqual((response.json()['slug'], response.json()['is_published']), ('hello-world', False))
        self.assertEqual(response.json()['id'], str(Post.objects.get(slug='hello-world').pk))

    def test_staff_can_edit_and_publish_a_draft(self):
        self.client.force_login(get_user_model().objects.create_user(username='editor', is_staff=True))
        draft = create_post('Draft', is_published=False)
        detail_url = reverse('api:post-detail', args=[draft.pk])

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

        post_page = self.client.get(post.get_absolute_url())
        category_page = self.client.get(post.category.get_absolute_url())
        home = self.client.get(reverse('main:index'))

        urls = post.cover_urls
        self.assertContains(post_page, f'src="{urls["post"]}"')
        self.assertContains(post_page, f'<meta property="og:image" content="http://testserver{urls["social"]}">')
        self.assertContains(post_page, f'src="{urls["thumb"]}"')  # the sidebar's latest posts
        self.assertContains(category_page, f'<img src="{urls["card"]}"')
        self.assertContains(home, f'<img src="{urls["card"]}"')

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


class ReadTimeMigrationTests(TransactionTestCase):
    before = [('blog', '0004_post_category_set_null')]
    after = [('blog', '0005_post_read_time_from_text')]

    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

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


class CategoryAPITests(TestCase):
    def test_lists_categories_with_their_latest_published_posts(self):
        category = create_category()
        create_post('Old', category=category)
        create_post('New', category=category)
        create_post('Draft', category=category, is_published=False)
        create_category('empty-topic')
        create_post('Only a draft', category=create_category('drafts-only'), is_published=False)

        response = self.client.get(reverse('api:categories'))

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
            data=[SimpleNamespace(b64_json=base64.b64encode(image_file(size=(1024, 1024)).read()).decode())]
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

    def test_attaches_a_generated_cover_at_every_size(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.draft_article()

            post = Post.objects.get(slug='ownership-in-rust')
            self.assertEqual(stored_image(post.cover.name), ('PNG', (1024, 1024)))
            self.assertEqual(list(post.cover_sizes['paths']), ['post', 'card', 'thumb', 'social'])

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
