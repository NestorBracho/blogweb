import html
import json
import posixpath
import re
from pathlib import Path
from unittest import mock

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.core import mail
from django.http import HttpResponse
from django.template import Context, Template
from django.templatetags.static import static
from django.test import RequestFactory, TestCase, override_settings
from django.urls import resolve, reverse
from django.utils import translation
from django.views.defaults import server_error

from config.middleware import ContentSecurityPolicyMiddleware
from config.testing import EmptyCacheMixin, create_category, create_post, reverse_in, structured_data
from config.throttling import FormThrottle

from . import seo
from .models import ContactRequest
from .views import HOME_PAGE_SIZE


def page_title(response):
    return html.unescape(re.search(r'<title>(.*?)</title>', response.content.decode()).group(1))


def meta(response, name):
    """The content of the page's <meta name="…"> or <meta property="…">."""
    match = re.search(rf'<meta (?:name|property)="{re.escape(name)}" content="([^"]*)">', response.content.decode())
    return html.unescape(match.group(1))


def inner_html(response, css_class):
    """What the page's first element with that class holds. It mustn't hold another element of its own tag."""
    match = re.search(rf'<(\w+) class="{css_class}">(.*?)</\1>', response.content.decode(), re.DOTALL)
    return match.group(2)


# The copy is free to change: these tests check who the page is about, its language and where it leads
class HomeTests(TestCase):
    def get_home(self, language):
        return self.client.get(reverse_in(language, 'main:index'))

    def test_intro_is_in_the_language_of_the_page(self):
        spanish = self.get_home('es')
        english = self.get_home('en')

        self.assertContains(spanish, '<html lang="es"')
        self.assertContains(english, '<html lang="en"')
        # Every paragraph, translated
        spanish_intro = re.findall(r'<p>(.*?)</p>', inner_html(spanish, 'hero__description'), re.DOTALL)
        english_intro = re.findall(r'<p>(.*?)</p>', inner_html(english, 'hero__description'), re.DOTALL)
        self.assertEqual(len(spanish_intro), len(english_intro))
        for spanish_paragraph, english_paragraph in zip(spanish_intro, english_intro, strict=True):
            self.assertNotEqual(spanish_paragraph, english_paragraph)

    def test_says_who_i_am_in_search_results_and_link_previews(self):
        for language in ['en', 'es']:
            with self.subTest(language=language):
                response = self.get_home(language)
                title = page_title(response)

                self.assertIn('Nestor Bracho', title)
                self.assertIn(settings.OWNER_ROLE, title)
                self.assertEqual(meta(response, 'og:title'), title)
                self.assertIn(settings.OWNER_ROLE, meta(response, 'description'))
                self.assertEqual(meta(response, 'og:description'), meta(response, 'description'))

    @override_settings(OWNER_ROLE='Staff Engineer')
    def test_the_role_is_set_in_one_place(self):
        home = self.client.get(reverse_in('es', 'main:index'))
        cv = self.client.get(reverse_in('es', 'main:cv'))

        self.assertIn('Staff Engineer', page_title(home))
        self.assertIn('Staff Engineer', meta(home, 'description'))
        self.assertIn('Staff Engineer', inner_html(home, 'hero__subtitle'))
        self.assertIn('Staff Engineer', inner_html(cv, 'cv__headline'))
        self.assertIn('Staff Engineer', meta(cv, 'description'))

    def test_points_from_the_role_to_the_personal_blog(self):
        for language in ['en', 'es']:
            with self.subTest(language=language):
                response = self.get_home(language)

                self.assertIn('<a href="#blog">', inner_html(response, 'hero__description'))
                self.assertContains(response, 'id="blog"')

    def test_footer_says_whose_site_it_is_in_each_language(self):
        spanish = inner_html(self.get_home('es'), 'footer__info__description')
        english = inner_html(self.get_home('en'), 'footer__info__description')

        self.assertIn('Nestor Bracho', spanish)
        self.assertIn('Nestor Bracho', english)
        self.assertNotEqual(spanish, english)

    def test_leads_to_the_cv_and_the_contact_form(self):
        response = self.client.get(reverse('main:index'))

        self.assertContains(response, f'href="{reverse("main:cv")}" class="button button--primary"')
        self.assertContains(response, f'href="{reverse("main:contact")}" class="button button--secondary"')


class HomePostsTests(TestCase):
    """The Binary Journal: the newest posts come with the page, and "Load more" adds the older ones."""

    def create_posts(self, count):
        # 'Post 0' is the newest
        for number in range(count):
            create_post(f'Post {number}', days_ago=number)

    def titles(self, response):
        return [post.title_en for post in response.context['post_list']]

    def post_link(self, language, number):
        return f'href="{reverse_in(language, "blog:post-detail", slug=f"post-{number}")}"'

    def test_the_newest_posts_come_with_the_page(self):
        self.create_posts(5)
        create_post('Draft', is_published=False)

        response = self.client.get(reverse_in('es', 'main:index'))

        self.assertEqual(self.titles(response), ['Post 0', 'Post 1', 'Post 2', 'Post 3'])
        self.assertContains(response, 'grid__post', count=4)
        self.assertContains(response, self.post_link('es', 3))
        self.assertNotContains(response, self.post_link('es', 4))
        self.assertNotContains(response, 'href="/es/post/draft"')

    def test_load_more_leads_to_the_next_page_without_javascript(self):
        self.create_posts(9)

        first = self.client.get(reverse_in('en', 'main:index'))
        second = self.client.get(reverse_in('en', 'main:index'), {'page': 2})
        last = self.client.get(reverse_in('en', 'main:index'), {'page': 3})

        self.assertContains(first, 'href="/en/?page=2#blog"')
        self.assertEqual(self.titles(second), ['Post 4', 'Post 5', 'Post 6', 'Post 7'])
        self.assertContains(second, 'href="/en/?page=3#blog"')
        self.assertEqual(self.titles(last), ['Post 8'])
        self.assertNotContains(last, 'load-more-posts')
        # Each page has its own address for search engines
        self.assertContains(second, '<link rel="canonical" href="http://testserver/en/?page=2">')

    def test_pages_past_the_last_are_not_found(self):
        self.create_posts(1)

        for page in ['2', 'two']:
            with self.subTest(page=page), self.assertLogs('django.request', 'WARNING'):
                self.assertEqual(self.client.get(reverse_in('en', 'main:index'), {'page': page}).status_code, 404)
                self.assertEqual(self.client.get(reverse_in('en', 'main:more-posts'), {'page': page}).status_code, 404)

    def test_load_more_asks_for_the_next_posts_alone(self):
        self.create_posts(9)

        home = self.client.get(reverse_in('es', 'main:index'))
        more = self.client.get(reverse_in('es', 'main:more-posts'), {'page': 2})
        last = self.client.get(reverse_in('es', 'main:more-posts'), {'page': 3})

        self.assertContains(home, f'hx-get="{reverse_in("es", "main:more-posts")}?page=2"')
        self.assertEqual(self.titles(more), ['Post 4', 'Post 5', 'Post 6', 'Post 7'])
        self.assertNotContains(more, '<html')
        # In the language of the page that asked
        self.assertContains(more, self.post_link('es', 4))
        # The block with the next link takes the place of the one that asked, and is empty after the last page
        self.assertContains(more, '<div id="bj-load-more" class="pagination animate" hx-swap-oob="true">')
        self.assertContains(more, f'hx-get="{reverse_in("es", "main:more-posts")}?page=3"')
        self.assertNotContains(last, 'load-more-posts')
        # A piece of a page: search engines index the home's own pages instead
        self.assertEqual(more.headers['X-Robots-Tag'], 'noindex')

    def test_load_more_says_when_the_posts_cannot_be_loaded(self):
        self.create_posts(5)

        spanish = self.client.get(reverse_in('es', 'main:index'))
        english = self.client.get(reverse_in('en', 'main:index'))

        self.assertContains(spanish, '<p class="load-more-error" role="alert" hidden>No se pudieron cargar')
        self.assertContains(english, '<p class="load-more-error" role="alert" hidden>The posts couldn\'t be loaded.')

    def test_scripts_are_files_of_the_site(self):
        response = self.client.get(reverse_in('en', 'main:index'))

        scripts = re.findall(r'<script src="([^"]+)"', response.content.decode())
        self.assertIn(static('js/htmx-2.0.11.min.js'), scripts)
        for script in scripts:
            with self.subTest(script=script):
                self.assertIsNotNone(finders.find(script.removeprefix(settings.STATIC_URL)))


class HackersHavenTests(TestCase):
    def test_shows_the_categories_with_the_newest_posts_and_their_latest_posts(self):
        quiet = create_category('quiet-topic', name_en='Quiet')
        busy = create_category('busy-topic', name_en='Busy')
        create_post('Old news', days_ago=30, category=quiet)
        for number in range(6):
            create_post(f'Busy {number}', days_ago=number, category=busy)
        create_post('Busy draft', category=busy, is_published=False)
        for number in range(4):
            create_post(f'Elsewhere {number}', days_ago=10 + number, category=create_category(f'topic-{number}'))

        response = self.client.get(reverse_in('en', 'main:index'))

        haven = response.context['hackers_haven']
        # The four with the newest posts, each with its five latest
        self.assertEqual([category.slug for category in haven], ['busy-topic', 'topic-0', 'topic-1', 'topic-2'])
        self.assertEqual([post.title_en for post in haven[0].latest_posts], [f'Busy {number}' for number in range(5)])
        self.assertContains(
            response,
            f'<a href="{reverse_in("en", "blog:category-detail", slug="busy-topic")}" class="section-tags__image"',
        )
        self.assertContains(response, f'<a href="{reverse_in("en", "blog:post-detail", slug="busy-4")}">Busy 4</a>')
        self.assertNotContains(response, 'href="/en/post/busy-draft"')
        self.assertNotContains(response, 'href="/en/post/old-news"')

    def test_has_no_placeholder_links_left_from_the_theme(self):
        for number in range(HOME_PAGE_SIZE + 1):
            create_post(f'Post {number}', category=create_category(f'topic-{number}'))

        response = self.client.get(reverse_in('en', 'main:index'))

        self.assertContains(response, 'Hacker’s Haven')
        self.assertNotContains(response, 'avoiding-common-javascript-mistakes')


class FewPostsTests(TestCase):
    """While every post fits on the home's first page, the lists that would only repeat them wait for more."""

    def get_pages(self, posts):
        for number in range(posts):
            create_post(f'Post {number}', days_ago=number, category=create_category(f'topic-{number}'))
        home = self.client.get(reverse_in('en', 'main:index'))
        post = self.client.get(reverse_in('en', 'blog:post-detail', slug='post-0'))
        return home, post

    def test_hackers_haven_and_the_sidebars_latest_posts_wait_for_more_posts(self):
        home, post = self.get_pages(HOME_PAGE_SIZE)

        self.assertNotContains(home, 'Hacker’s Haven')
        for page in [home, post]:
            self.assertNotContains(page, 'widget-featured-posts')
            # The footer keeps its own list
            self.assertContains(page, '<h3 class="footer__title">Recent Posts</h3>')

    def test_they_show_up_with_one_post_more(self):
        home, post = self.get_pages(HOME_PAGE_SIZE + 1)

        self.assertContains(home, 'Hacker’s Haven')
        for page in [home, post]:
            self.assertContains(page, 'widget-featured-posts')


class BrandTests(TestCase):
    wordmark = '<span class="brand-wordmark"><span class="brand-wordmark__prefix" aria-hidden="true">~/</span>bracho'

    def test_header_and_footer_show_the_wordmark(self):
        response = self.client.get(reverse('main:index'))

        self.assertContains(response, self.wordmark, count=2)

    def test_logo_link_has_a_name_in_each_language(self):
        spanish = self.client.get(reverse_in('es', 'main:index'))
        english = self.client.get(reverse_in('en', 'main:index'))

        self.assertContains(spanish, 'aria-label="Bracho, inicio"')
        self.assertContains(english, 'aria-label="Bracho, home"')


class HeaderTests(TestCase):
    """The header's controls are buttons, so they work with a keyboard and screen readers can name them."""

    def get_home(self, language):
        return self.client.get(reverse_in(language, 'main:index'))

    def test_controls_are_buttons(self):
        response = self.get_home('en')

        for control in ['hamburger', 'toggle-theme', 'dropdown-toggle', 'search-button', 'search__close']:
            self.assertContains(response, f'<button type="button" class="{control}"')

    def test_controls_are_named_in_each_language(self):
        response = self.get_home('es')

        self.assertContains(response, 'aria-label="Menú"')
        self.assertContains(response, 'aria-label="Modo oscuro"')
        self.assertContains(response, '<span class="screen-reader-text">Idioma:</span>')
        self.assertContains(response, 'aria-label="Cerrar búsqueda"')
        self.assertContains(response, 'placeholder="Escribe para buscar..."')

    def test_language_menu_is_a_form_that_needs_no_javascript(self):
        page = self.client.get(reverse_in('en', 'main:cv'))

        self.assertContains(page, f'<form action="{reverse_in("en", "set_language")}" method="post"')
        self.assertContains(page, f'<input type="hidden" name="next" value="{reverse_in("en", "main:cv")}">')
        self.assertContains(page, '<button type="submit" name="language" value="es"')

    def test_language_menu_opens_the_same_page_in_the_other_language(self):
        for current, chosen in [('en', 'es'), ('es', 'en')]:
            with self.subTest(chosen=chosen):
                # Even when the language cookie disagrees with the page: the form is sent from the page's language
                self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = chosen
                page = f'{reverse_in(current, "main:cv")}?ref=menu'

                response = self.client.post(reverse_in(current, 'set_language'), {'language': chosen, 'next': page})

                self.assertRedirects(
                    response, f'{reverse_in(chosen, "main:cv")}?ref=menu', fetch_redirect_response=False
                )
                self.assertEqual(self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, chosen)


class LanguageInTheURLTests(TestCase):
    """Pages live under /en/ and /es/; a path without a language goes to the visitor's (docs/adr/0006)."""

    def assertRedirectsTo(self, response, url):
        self.assertRedirects(response, url, status_code=302, fetch_redirect_response=False)

    def test_visitors_who_ask_for_neither_language_get_english(self):
        # Crawlers and link previews send no Accept-Language at all
        for headers in [{}, {'Accept-Language': 'fr-FR,fr;q=0.9,de;q=0.8'}]:
            with self.subTest(headers=headers):
                self.assertRedirectsTo(self.client.get('/', headers=headers), '/en/')

    def test_spanish_browsers_get_spanish(self):
        response = self.client.get('/cv/', headers={'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8'})

        self.assertRedirectsTo(response, '/es/cv/')

    def test_the_language_chosen_in_the_menu_wins_over_the_browser(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = 'es'

        response = self.client.get('/cv/', headers={'Accept-Language': 'en'})

        self.assertRedirectsTo(response, '/es/cv/')

    def test_redirects_keep_the_query_string_and_are_not_shared_between_visitors(self):
        response = self.client.get('/?utm_source=linkedin')

        self.assertRedirectsTo(response, '/en/?utm_source=linkedin')
        self.assertIn('Accept-Language', response['Vary'])
        self.assertIn('Cookie', response['Vary'])

    def test_each_language_has_its_own_address(self):
        for language in ['en', 'es']:
            with self.subTest(language=language):
                response = self.client.get(f'/{language}/', headers={'Accept-Language': 'fr'})

                self.assertContains(response, f'<html lang="{language}"')
                # The address alone decides the language, so caches don't have to tell browsers apart
                self.assertNotIn('Accept-Language', response.get('Vary', ''))

    def test_the_admin_api_sitemap_and_robots_stay_at_the_root(self):
        for name in ['admin:login', 'api:post-list', 'sitemap', 'robots']:
            with self.subTest(name=name):
                url = reverse(name)

                self.assertFalse(url.startswith(('/en/', '/es/')))
                self.assertEqual(self.client.get(url).status_code, 200)


class ContentSecurityPolicyTests(TestCase):
    def test_pages_only_run_the_sites_own_scripts(self):
        response = self.client.get(reverse('main:index'))

        policy = response.headers['Content-Security-Policy']
        self.assertIn("script-src 'self';", policy)
        self.assertIn("object-src 'none';", policy)
        self.assertIn("frame-ancestors 'none'", policy)

    def test_pages_have_no_inline_scripts_for_the_policy_to_block(self):
        pages = ['main:index', 'main:about', 'main:cv', 'main:contact', 'main:privacy', 'admin:login']

        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(reverse(page))

                # JSON-LD blocks are data that browsers never run, so the policy doesn't apply to them
                inline_script = r'<script(?![^>]*\b(?:src=|type="application/ld\+json"))[^>]*>'
                self.assertNotRegex(response.content.decode(), inline_script)

    def test_leaves_alone_a_policy_set_by_the_view(self):
        own_policy = HttpResponse(headers={'Content-Security-Policy': "default-src 'none'"})
        middleware = ContentSecurityPolicyMiddleware(lambda request: own_policy)

        response = middleware(RequestFactory().get('/'))

        self.assertEqual(response.headers['Content-Security-Policy'], "default-src 'none'")

    @override_settings(SECURE_CSP={})
    def test_an_empty_setting_sends_no_policy(self):
        response = self.client.get(reverse('main:index'))

        self.assertNotIn('Content-Security-Policy', response.headers)


class FontTests(TestCase):
    def test_fonts_only_come_from_the_site_itself(self):
        policy = self.client.get(reverse('main:index')).headers['Content-Security-Policy']

        # Without a font-src of its own, default-src 'self' applies to fonts
        self.assertIn("default-src 'self';", policy)
        self.assertNotIn('font-src', policy)
        self.assertIn("style-src 'self' 'unsafe-inline';", policy)

    def test_every_font_the_stylesheets_declare_is_a_file_of_the_site(self):
        for stylesheet in ['css/fonts.css', 'css/main.css']:
            for url in re.findall(r'url\(([^)]+)\)', Path(finders.find(stylesheet)).read_text()):
                with self.subTest(stylesheet=stylesheet, url=url):
                    self.assertIsNotNone(finders.find(posixpath.normpath(posixpath.join('css', url))))

    def test_preloaded_fonts_are_ones_the_stylesheet_uses(self):
        fonts_css = Path(finders.find('css/fonts.css')).read_text()

        # The contact page doesn't extend base.html, so it gets its own check
        for page in ['main:index', 'main:contact']:
            response = self.client.get(reverse(page))
            preloads = re.findall(r'<link rel="preload" href="([^"]+)" as="font"', response.content.decode())

            self.assertEqual(len(preloads), 2)
            for url in preloads:
                with self.subTest(page=page, url=url):
                    self.assertIn(f'url(../{url.removeprefix(settings.STATIC_URL)})', fonts_css)

    def test_the_icon_fonts_have_every_icon_the_site_uses(self):
        icons_file = Path(finders.find('fonts/fontawesome/icons.txt'))
        listed = {tuple(line.split()) for line in icons_file.read_text().splitlines() if not line.startswith('#')}
        # The templates and scripts of the project and of its apps
        folders = [settings.BASE_DIR, *(Path(app.path) for app in apps.get_app_configs())]
        used = set()
        for folder in folders:
            if folder.is_relative_to(settings.BASE_DIR):
                for path in [*folder.glob('templates/**/*.html'), *folder.glob('static/**/*.js')]:
                    used.update(re.findall(r'\bfa-(solid|regular|brands) fa-([a-z0-9-]+)', path.read_text()))

        self.assertIn(('brands', 'github'), used)
        self.assertEqual(used - listed, set(), f'add them to {icons_file} and run tools/subset_fonts.py')


class FaviconTests(TestCase):
    def test_root_favicon_redirects_to_the_static_file(self):
        response = self.client.get('/favicon.ico')

        self.assertRedirects(response, static('favicon/favicon.ico'), status_code=302, fetch_redirect_response=False)

    def test_every_page_declares_the_icons_and_theme_color(self):
        # The contact page doesn't extend base.html, so it gets its own check
        for url in [reverse('main:index'), reverse('main:contact')]:
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertContains(response, f'<link rel="manifest" href="{static("favicon/site.webmanifest")}"/>')
                self.assertContains(response, '<meta name="theme-color" content="#10141f">')

    def test_manifest_icons_are_relative_to_the_manifest_and_exist(self):
        manifest = json.loads(Path(finders.find('favicon/site.webmanifest')).read_text())

        for icon in manifest['icons']:
            with self.subTest(icon=icon['src']):
                self.assertFalse(icon['src'].startswith('/'))
                self.assertIsNotNone(finders.find(f'favicon/{icon["src"]}'))


class SocialImageTests(TestCase):
    def test_pages_without_their_own_image_use_the_brand_one(self):
        response = self.client.get(reverse('main:cv'))

        image_url = f'http://testserver{static("images/og-default.png")}'
        self.assertContains(response, f'<meta property="og:image" content="{image_url}">')
        self.assertContains(response, f'<meta property="twitter:image:src" content="{image_url}">')

    def test_pages_with_their_own_image_keep_it(self):
        response = self.client.get(reverse('main:contact'))

        image_url = f'http://testserver{static("images/40.jpg")}'
        self.assertContains(response, f'<meta property="og:image" content="{image_url}">')


class ErrorPageTests(TestCase):
    def test_server_error_page_renders_without_a_request(self):
        # Django renders 500.html with no context at all: no request and no context processors
        with translation.override('en'):
            response = server_error(RequestFactory().get('/'))

        self.assertContains(response, '<title>Server Malfunction - Nestor Bracho</title>', status_code=500)
        self.assertContains(response, 'Back to homepage', status_code=500)

    def test_not_found_page_has_its_own_title_and_nothing_to_index(self):
        # A path nothing matches, and a page whose view finds nothing to show
        for url in ['/en/no-such-page/', reverse_in('en', 'blog:post-detail', slug='no-such-post')]:
            with self.subTest(url=url):
                with self.assertLogs('django.request', 'WARNING'):
                    response = self.client.get(url)

                self.assertContains(response, '<title>Page not found - Nestor Bracho</title>', status_code=404)
                self.assertContains(response, 'Back to homepage', status_code=404)
                self.assertNotContains(response, 'rel="canonical"', status_code=404)
                self.assertNotContains(response, 'hreflang', status_code=404)
                self.assertNotContains(response, 'og:url', status_code=404)

        with self.assertLogs('django.request', 'WARNING'):
            spanish = self.client.get('/es/no-such-page/')
        self.assertContains(spanish, '<title>Página no encontrada - Nestor Bracho</title>', status_code=404)


class SearchAndLinkPreviewTests(TestCase):
    """What search engines and link previews read in each page's <head>."""

    def test_each_page_points_to_itself_in_each_language(self):
        response = self.client.get(reverse_in('es', 'main:cv'))

        self.assertContains(response, '<link rel="canonical" href="http://testserver/es/cv/">')
        self.assertContains(response, '<link rel="alternate" hreflang="en" href="http://testserver/en/cv/">')
        self.assertContains(response, '<link rel="alternate" hreflang="es" href="http://testserver/es/cv/">')
        # Everyone else gets the address without a language, which sends them to theirs
        self.assertContains(response, '<link rel="alternate" hreflang="x-default" href="http://testserver/cv/">')
        self.assertContains(response, '<meta property="og:url" content="http://testserver/es/cv/">')
        self.assertContains(response, '<meta property="og:locale" content="es_ES">')
        self.assertContains(response, '<meta property="og:locale:alternate" content="en_US">')

    def test_the_canonical_address_leaves_out_how_visitors_arrived(self):
        response = self.client.get(reverse_in('en', 'main:index'), {'utm_source': 'linkedin', 'fbclid': 'abc'})

        self.assertContains(response, '<link rel="canonical" href="http://testserver/en/">')
        self.assertContains(response, '<link rel="alternate" hreflang="es" href="http://testserver/es/">')

    def test_previews_name_the_site_and_size_the_brand_image(self):
        response = self.client.get(reverse_in('en', 'main:about'))

        self.assertContains(response, '<meta property="og:site_name" content="Nestor Bracho">')
        self.assertContains(response, '<meta property="og:type" content="website">')
        self.assertContains(response, '<meta property="og:image:width" content="1200">')
        self.assertContains(response, '<meta property="og:image:height" content="630">')

    def test_pages_with_their_own_image_leave_its_size_to_the_preview(self):
        response = self.client.get(reverse_in('en', 'main:contact'))

        self.assertNotContains(response, 'og:image:width')

    def test_only_pages_in_a_language_have_other_versions(self):
        # Django renders the 500 page without a request, and the API lives outside the language prefixes
        api = RequestFactory().get('/api/post/')
        api.resolver_match = resolve('/api/post/')

        self.assertIsNone(seo.page_urls(None))
        self.assertIsNone(seo.page_urls(api))

    def test_absolute_urls_fall_back_to_relative_ones_without_a_request(self):
        template = Template('{% load main_tags %}{% absolute_uri "/static/images/og-default.png" %}')

        self.assertEqual(template.render(Context()), '/static/images/og-default.png')

    @override_settings(OWNER_ROLE='Staff Engineer', OWNER_EMAIL='nestor@example.com')
    def test_home_page_says_who_the_site_is_about(self):
        data = structured_data(self.client.get(reverse_in('en', 'main:index')))

        self.assertEqual(data['@context'], 'https://schema.org')
        self.assertEqual((data['@type'], data['name'], data['jobTitle']), ('Person', 'Nestor Bracho', 'Staff Engineer'))
        self.assertEqual(data['url'], 'http://testserver/en/')
        self.assertIn('https://github.com/NestorBracho', data['sameAs'])
        # Contact details stay off the markup
        self.assertNotIn('nestor@example.com', json.dumps(data))

    def test_cv_is_a_profile_of_the_same_person(self):
        home = structured_data(self.client.get(reverse_in('en', 'main:index')))
        cv = structured_data(self.client.get(reverse_in('es', 'main:cv')))

        self.assertEqual((cv['@type'], cv['inLanguage']), ('ProfilePage', 'es'))
        self.assertEqual(cv['url'], 'http://testserver/es/cv/')
        self.assertEqual(cv['mainEntity']['@id'], home['@id'])


class PrivacyViewTests(TestCase):
    def test_shows_the_whole_policy_in_each_language(self):
        spanish = self.client.get(reverse_in('es', 'main:privacy'))
        english = self.client.get(reverse_in('en', 'main:privacy'))

        self.assertContains(spanish, '<title>Política de privacidad - Nestor Bracho</title>')
        self.assertContains(spanish, 'Quién es responsable')
        self.assertNotContains(spanish, 'Who is responsible')
        self.assertContains(english, '<title>Privacy policy - Nestor Bracho</title>')
        self.assertContains(english, 'Who is responsible')

    @override_settings(OWNER_EMAIL='nestor@example.com')
    def test_gives_the_owner_email_when_configured(self):
        response = self.client.get(reverse('main:privacy'))

        self.assertContains(response, 'href="mailto:nestor@example.com"')

    def test_is_linked_from_every_form_and_the_sitemap(self):
        privacy_link = f'href="{reverse("main:privacy")}"'

        self.assertContains(self.client.get(reverse('main:contact')), privacy_link)
        # The home page has the newsletter form and the footer
        self.assertContains(self.client.get(reverse('main:index')), privacy_link, count=2)
        self.assertContains(self.client.get(reverse('sitemap')), f'http://testserver{reverse("main:privacy")}')


class RobotsTxtTests(TestCase):
    def test_points_crawlers_to_the_sitemap(self):
        response = self.client.get(reverse('robots'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertContains(response, f'Sitemap: http://testserver{reverse("sitemap")}')


class AboutViewTests(TestCase):
    def test_uses_its_own_meta_tags(self):
        response = self.client.get(reverse_in('en', 'main:about'))

        self.assertContains(response, '<title>About Me - Nestor Bracho</title>')
        self.assertContains(response, '<meta property="og:image" content="http://testserver/static/')

    def test_spanish_title_is_spelled_right(self):
        response = self.client.get(reverse_in('es', 'main:about'))

        self.assertContains(response, '<title>Sobre mí - Nestor Bracho</title>')


@override_settings(OWNER_CV_PDF_URLS={'en': '/media/cv/cv-en.pdf', 'es': '/media/cv/cv-es.pdf'})
class CVViewTests(TestCase):
    def test_shows_the_whole_cv_in_each_language(self):
        spanish = self.client.get(reverse_in('es', 'main:cv'))
        english = self.client.get(reverse_in('en', 'main:cv'))

        self.assertContains(spanish, 'Experiencia profesional')
        self.assertNotContains(spanish, 'Professional experience')
        self.assertContains(english, 'Professional experience')
        self.assertContains(english, '<title>CV - Nestor Bracho</title>')

    def test_explains_the_jobs_that_overlap(self):
        # Freelance work ran alongside other jobs: each one says so next to its dates, or they read like a mistake
        jobs = {
            'en': [
                (
                    '<strong>World Bank Group</strong> · Contract · Madrid, remote · Jun 2023 – Present',
                    'In parallel with my role at Selia until Sep 2023 and with Ekwi-three in 2024.',
                ),
                (
                    '<strong>Ekwi-three GmbH</strong> · Freelance · Remote · May 2024 – Dec 2024',
                    'In parallel with my World Bank Group contract.',
                ),
                (
                    '<strong>Selia</strong> · Full-time · Remote · Jan 2022 – Sep 2023',
                    'From Dec 2022, in parallel with my World Bank Group projects.',
                ),
                (
                    '<strong>World Bank Group</strong> · Freelance · Remote · Dec 2022 – Mar 2023',
                    'In parallel with my full-time role at Selia.',
                ),
            ],
            'es': [
                (
                    '<strong>Grupo Banco Mundial</strong> · Contrato · Madrid, remoto · jun 2023 – actualidad',
                    'En paralelo con mi puesto en Selia hasta sep 2023 y con Ekwi-three en 2024.',
                ),
                (
                    '<strong>Ekwi-three GmbH</strong> · Freelance · Remoto · may 2024 – dic 2024',
                    'En paralelo con mi contrato en el Grupo Banco Mundial.',
                ),
                (
                    '<strong>Selia</strong> · Jornada completa · Remoto · ene 2022 – sep 2023',
                    'Desde dic 2022, en paralelo con mis proyectos para el Grupo Banco Mundial.',
                ),
                (
                    '<strong>Grupo Banco Mundial</strong> · Freelance · Remoto · dic 2022 – mar 2023',
                    'En paralelo con mi puesto a jornada completa en Selia.',
                ),
            ],
        }
        for language, notes in jobs.items():
            response = self.client.get(reverse_in(language, 'main:cv'))

            for meta, note in notes:
                with self.subTest(language=language, note=note):
                    expected = f'<p class="cv__job-meta">{meta}<br><span class="cv__note">{note}</span></p>'

                    self.assertContains(response, expected, html=True)

    def test_offers_the_pdf_in_the_page_language(self):
        spanish = self.client.get(reverse_in('es', 'main:cv'))
        english = self.client.get(reverse_in('en', 'main:cv'))

        self.assertContains(spanish, 'href="/media/cv/cv-es.pdf"')
        self.assertContains(english, 'href="/media/cv/cv-en.pdf"')

    @override_settings(OWNER_CV_PDF_URLS={'en': '', 'es': ''})
    def test_hides_the_download_without_a_pdf(self):
        response = self.client.get(reverse_in('en', 'main:cv'))

        self.assertNotContains(response, 'Download PDF')

    @override_settings(OWNER_EMAIL='nestor@example.com', OWNER_LOCATION='Madrid, Spain')
    def test_gives_the_contact_details_when_configured(self):
        response = self.client.get(reverse_in('en', 'main:cv'))

        self.assertContains(response, 'href="mailto:nestor@example.com"')
        self.assertContains(response, 'Madrid, Spain')

    def test_is_linked_from_the_menu_and_the_sitemap(self):
        home = self.client.get(reverse_in('en', 'main:index'))
        sitemap = self.client.get(reverse('sitemap'))

        self.assertContains(home, f'href="{reverse_in("en", "main:cv")}"')
        for language in ['en', 'es']:
            self.assertContains(sitemap, f'<loc>http://testserver{reverse_in(language, "main:cv")}</loc>')

    def test_the_old_resume_post_redirects_here(self):
        # Old links have no language: first to the visitor's, then for good to the CV in that language
        response = self.client.get('/post/resume')
        self.assertRedirects(response, '/en/post/resume', status_code=302, fetch_redirect_response=False)

        for language in ['en', 'es']:
            with self.subTest(language=language):
                response = self.client.get(f'/{language}/post/resume')

                self.assertRedirects(response, reverse_in(language, 'main:cv'), status_code=301)


@override_settings(OWNER_GITHUB_URL='https://github.com/example', OWNER_LINKEDIN_URL='')
class SocialLinksTests(TestCase):
    def test_links_configured_profiles_only(self):
        response = self.client.get(reverse('main:index'))

        # Footer and sidebar both render the list; the intro only links the profiles when both are set
        self.assertContains(response, 'href="https://github.com/example"', count=2)
        self.assertNotContains(response, 'fa-linkedin"')

    @override_settings(OWNER_LINKEDIN_URL='https://www.linkedin.com/in/example')
    def test_links_linkedin_when_configured(self):
        response = self.client.get(reverse('main:index'))

        # Footer, sidebar and the intro
        self.assertContains(response, 'href="https://www.linkedin.com/in/example"', count=3)


class ContactFormViewTests(EmptyCacheMixin, TestCase):
    data = {'name': 'Ada', 'email': 'ada@example.com', 'message': 'Hello!'}

    def test_stores_the_request_and_emails_it(self):
        response = self.client.post(reverse('main:contact'), self.data)

        self.assertRedirects(response, reverse('main:index'), fetch_redirect_response=False)
        self.assertTrue(ContactRequest.objects.filter(email='ada@example.com').exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].reply_to, ['ada@example.com'])

    def test_gives_the_form_back_with_what_was_typed_and_what_to_fix(self):
        response = self.client.post(reverse_in('en', 'main:contact'), {**self.data, 'email': 'ada@'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Ada"')
        self.assertContains(response, '>Hello!</textarea>')
        self.assertContains(response, 'aria-describedby="form-email-error"')
        self.assertContains(response, 'Enter a valid email address.')
        self.assertFalse(ContactRequest.objects.exists())
        self.assertEqual(mail.outbox, [])

    def test_is_marked_with_the_page_language(self):
        response = self.client.get(reverse_in('es', 'main:contact'))

        self.assertContains(response, '<html lang="es"')

    def test_the_photo_loads_first(self):
        # It is the largest thing on the first screen at desktop widths
        response = self.client.get(reverse('main:contact'))

        self.assertContains(response, 'fetchpriority="high"')
        self.assertNotContains(response, 'loading="lazy"')

    def test_ignores_bots_that_fill_the_hidden_field(self):
        response = self.client.post(reverse('main:contact'), {**self.data, 'contact_me_by_fax_only': 'spam'})

        self.assertRedirects(response, reverse('main:index'), fetch_redirect_response=False)
        self.assertFalse(ContactRequest.objects.exists())
        self.assertEqual(mail.outbox, [])

    def test_keeps_the_request_when_the_email_fails(self):
        with (
            mock.patch('main.forms.EmailMultiAlternatives.send', side_effect=OSError('SMTP is down')),
            self.assertLogs('main.forms', level='ERROR'),
        ):
            response = self.client.post(reverse('main:contact'), self.data)

        self.assertRedirects(response, reverse('main:index'), fetch_redirect_response=False)
        self.assertTrue(ContactRequest.objects.filter(email='ada@example.com').exists())

    def test_limits_how_many_requests_each_visitor_sends(self):
        allowed = FormThrottle('contact').num_requests
        visitor = {'CF-Connecting-IP': '203.0.113.7'}
        for _ in range(allowed):
            self.client.post(reverse('main:contact'), self.data, headers=visitor)

        with self.assertLogs('django.request', 'WARNING'):
            too_many = self.client.post(
                reverse_in('es', 'main:contact'), {**self.data, 'message': 'Una más'}, headers=visitor
            )
        someone_else = self.client.post(reverse('main:contact'), self.data, headers={'CF-Connecting-IP': '203.0.113.8'})

        # The form comes back in the page's language, with what was typed
        self.assertContains(too_many, 'Has enviado varios mensajes en poco tiempo', status_code=429)
        self.assertContains(too_many, 'value="Ada"', status_code=429)
        self.assertContains(too_many, '>Una más</textarea>', status_code=429)
        self.assertFalse(ContactRequest.objects.filter(message='Una más').exists())
        self.assertRedirects(someone_else, reverse('main:index'), fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), allowed + 1)


class ContactRequestAdminTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser('admin'))
        self.request = ContactRequest.objects.create(name='Ada', email='ada@example.com', message='Hello!')

    def test_requests_can_be_read_but_not_created(self):
        for url in [
            reverse('admin:main_contactrequest_changelist'),
            reverse('admin:main_contactrequest_change', args=[self.request.pk]),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

        # Django logs the refusal with its traceback
        with self.assertLogs('django.request', 'WARNING'):
            self.assertEqual(self.client.get(reverse('admin:main_contactrequest_add')).status_code, 403)
