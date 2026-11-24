import datetime
import html
import itertools
import json
import os
import posixpath
import re
import runpy
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
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import resolve, reverse
from django.utils import translation
from django.views.defaults import server_error

from blog.covers import SOCIAL_SIZE
from blog.listing import POSTS_PAGE_SIZE
from config.context_processors import years_of_experience
from config.middleware import ContentSecurityPolicyMiddleware
from config.testing import EmptyCacheMixin, create_category, create_post, reverse_in, structured_data
from config.throttling import FormThrottle

from . import cases, seo
from .models import ContactRequest


def page_title(response):
    return html.unescape(re.search(r'<title>(.*?)</title>', response.content.decode()).group(1))


def meta(response, name):
    """The content of the page's <meta name="…"> or <meta property="…">."""
    match = re.search(rf'<meta (?:name|property)="{re.escape(name)}" content="([^"]*)">', response.content.decode())
    return html.unescape(match.group(1))


def inner_html(response, css_class):
    """What the page's first element with that class holds. It mustn't hold another element of its own tag."""
    match = re.search(rf'<(\w+) class="{css_class}"[^>]*>(.*?)</\1>', response.content.decode(), re.DOTALL)
    return match.group(2)


def offer_texts(response):
    """The texts of the home's "What I offer" blocks, in order."""
    return [html.unescape(text) for text in re.findall(r'<p class="offer__text">(.*?)</p>', response.content.decode())]


def stylesheets(response):
    return re.findall(r'<link rel="stylesheet" href="([^"]+)"', response.content.decode())


def scripts(response):
    return re.findall(r'<script src="([^"]+)"', response.content.decode())


def headings(response):
    """The levels of the page's headings, in order: [1, 2, 3, 2...]."""
    return [int(level) for level in re.findall(r'<h([1-6])[\s>]', response.content.decode())]


def visible_text(response):
    """The page's text as visitors read it: no <head>, tags, comments or scripts."""
    content = response.content.decode().split('<body', 1)[1]
    content = re.sub(r'<script.*?</script>|<!--.*?-->', '', content, flags=re.DOTALL)
    return html.unescape(re.sub(r'<[^>]+>', ' ', content))


# The main site's pages, on its own layout (templates/site.html)
MAIN_SITE_PAGES = ['main:index', 'main:about', 'main:cv', 'main:contact', 'main:privacy']


# The copy is free to change: these tests check who the page is about, its language and where it leads
class HomeTests(TestCase):
    def get_home(self, language):
        return self.client.get(reverse_in(language, 'main:index'))

    def test_headline_is_in_the_language_of_the_page(self):
        spanish = self.get_home('es')
        english = self.get_home('en')

        self.assertContains(spanish, '<html lang="es"')
        self.assertContains(english, '<html lang="en"')
        self.assertContains(spanish, 'Diseño y construyo plataformas web y sus backends')
        self.assertContains(english, 'I design and build web platforms and their backends')
        self.assertNotEqual(inner_html(spanish, 'hero__lede'), inner_html(english, 'hero__lede'))

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
                self.assertEqual(meta(response, 'twitter:description'), meta(response, 'description'))
                self.assertEqual(structured_data(response)['description'], meta(response, 'description'))

    def test_describes_the_page_as_docs_home_cases_writes_it(self):
        years = years_of_experience()
        descriptions = {
            'en': (
                f'Senior Software Engineer with more than {years} years building web platforms with Python and '
                'Django. Three years for the World Bank Group; now freelance, with AI agent-driven development.'
            ),
            'es': (
                f'Senior Software Engineer con más de {years} años construyendo plataformas web con Python y '
                'Django. Tres años para el Grupo Banco Mundial; hoy, freelance con desarrollo dirigido por agentes '
                'de IA.'
            ),
        }
        for language, description in descriptions.items():
            with self.subTest(language=language):
                self.assertEqual(meta(self.get_home(language), 'description'), description)

    def test_pages_without_a_description_of_their_own_use_the_sites(self):
        home = self.get_home('es')
        cases = self.client.get(reverse_in('es', 'main:case-detail', slug='this-site'))

        self.assertIn('hoy, freelance', meta(home, 'description'))
        # A case's summary stands in for it on its page
        self.assertNotEqual(meta(cases, 'description'), meta(home, 'description'))

    def test_speaks_of_the_world_bank_in_the_past(self):
        for language, current in [
            ('en', ['currently for the World Bank', 'Consultant for the World Bank', '2023 to present']),
            ('es', ['actualmente, para el Grupo Banco Mundial', 'Consultor para el Grupo', '2023 a hoy']),
        ]:
            with self.subTest(language=language):
                response = self.get_home(language)
                content = html.unescape(response.content.decode())

                for phrase in current:
                    self.assertNotIn(phrase, content)
                self.assertNotIn('World Bank', ' '.join(offer_texts(response)))

    def test_the_lede_says_he_now_works_freelance(self):
        years = years_of_experience()
        ledes = {
            'en': (
                f'More than {years} years with Python and Django, three of them as an architect and developer for the '
                'World Bank Group. I now work as a freelancer and build complete systems with AI agents, under '
                'specification and human review.'
            ),
            'es': (
                f'Más de {years} años con Python y Django, tres de ellos como arquitecto y desarrollador para el Grupo '
                'Banco Mundial. Hoy trabajo como freelance y construyo sistemas completos con agentes de IA, bajo '
                'especificación y revisión humana.'
            ),
        }
        for language, lede in ledes.items():
            with self.subTest(language=language):
                self.assertEqual(html.unescape(inner_html(self.get_home(language), 'hero__lede')), lede)

    def test_offers_ai_with_the_latest_example(self):
        for language, example in [
            ('en', 'Most recently: a financial analysis service that explains the dashboards of a rental management'),
            ('es', 'Lo más reciente: un servicio de análisis financiero que explica los paneles de una plataforma'),
        ]:
            with self.subTest(language=language):
                self.assertIn(example, offer_texts(self.get_home(language))[2])

    def test_the_profile_card_gives_the_english_level(self):
        english = inner_html(self.get_home('en'), 'profile__list')
        spanish = inner_html(self.get_home('es'), 'profile__list')

        self.assertRegex(english, r'<dt>languages</dt>\s*<dd>Native Spanish · English B2</dd>')
        self.assertRegex(spanish, r'<dt>idiomas</dt>\s*<dd>Español nativo · Inglés B2</dd>')

    def test_the_role_is_senior_software_engineer(self):
        self.assertEqual(settings.OWNER_ROLE, 'Senior Software Engineer')

    @override_settings(OWNER_ROLE='Staff Engineer')
    def test_the_role_is_set_in_one_place(self):
        home = self.client.get(reverse_in('es', 'main:index'))
        cv = self.client.get(reverse_in('es', 'main:cv'))

        self.assertIn('Staff Engineer', page_title(home))
        self.assertIn('Staff Engineer', meta(home, 'description'))
        self.assertIn('Staff Engineer', inner_html(home, 'hero__kicker'))
        self.assertIn('<dd>Staff Engineer</dd>', inner_html(home, 'profile__list'))
        self.assertIn('Staff Engineer', inner_html(cv, 'cv__headline'))
        self.assertIn('Staff Engineer', meta(cv, 'description'))
        self.assertIn('Staff Engineer', page_title(cv))

    @override_settings(OWNER_CAREER_START_YEAR=2000)
    def test_the_years_of_experience_are_set_in_one_place(self):
        years = years_of_experience()
        self.assertEqual(years, datetime.date.today().year - 2000)

        for language, phrase in [('en', f'more than {years} years'), ('es', f'más de {years} años')]:
            with self.subTest(language=language):
                home = self.get_home(language)
                cv = self.client.get(reverse_in(language, 'main:cv'))

                self.assertIn(phrase, inner_html(home, 'hero__lede').lower())
                self.assertIn(phrase, inner_html(home, 'profile__list').lower())
                self.assertIn(phrase, meta(home, 'description'))
                self.assertIn(phrase, meta(cv, 'description'))
                self.assertContains(cv, f'{years}')

    @override_settings(OWNER_LOCATIONS={'en': 'Madrid, Spain', 'es': 'Madrid, España'})
    def test_the_profile_card_takes_the_location_from_the_settings(self):
        english = inner_html(self.get_home('en'), 'profile__list')
        spanish = inner_html(self.get_home('es'), 'profile__list')

        self.assertRegex(english, r'<dt>location</dt>\s*<dd>Madrid, Spain</dd>')
        self.assertRegex(spanish, r'<dt>ubicación</dt>\s*<dd>Madrid, España</dd>')

    @override_settings(OWNER_LOCATIONS={'en': '', 'es': ''})
    def test_the_profile_card_leaves_out_what_is_not_set(self):
        card = inner_html(self.get_home('en'), 'profile__list')

        # No location without one, and no availability row until Nestor confirms it
        self.assertEqual(
            re.findall(r'<dt>([^<]+)</dt>', card), ['role', 'stack', 'ai', 'experience', 'mode', 'languages']
        )

    def test_names_the_clients_in_text(self):
        english = inner_html(self.get_home('en'), 'clients__list')
        spanish = inner_html(self.get_home('es'), 'clients__list')

        self.assertEqual(
            re.findall(r'<li>([^<]+)</li>', english), ['World Bank Group', 'Nokia', 'Selia', 'Ekwi-three', 'IUCN']
        )
        self.assertEqual(
            re.findall(r'<li>([^<]+)</li>', spanish), ['Grupo Banco Mundial', 'Nokia', 'Selia', 'Ekwi-three', 'UICN']
        )

    def test_has_the_sections_of_the_brief_in_order(self):
        create_post('A post')
        content = self.get_home('en').content.decode()

        positions = [
            content.index(marker)
            for marker in [
                'class="site-header"',
                'class="hero"',
                'class="clients"',
                'id="cases"',
                'id="how-i-work"',
                'id="services"',
                'id="contact"',
                'id="blog"',
                'class="site-footer"',
            ]
        ]
        self.assertEqual(positions, sorted(positions))

    def test_leads_to_the_cv_and_the_contact_form(self):
        response = self.client.get(reverse('main:index'))

        # The hero's buttons, and again in the contact section
        self.assertContains(response, f'<a class="button button--primary" href="{reverse("main:contact")}">', count=2)
        self.assertContains(response, f'<a class="button" href="{reverse("main:cv")}">', count=2)

    def test_how_i_work_links_to_the_crm_case(self):
        response = self.get_home('es')

        crm = reverse_in('es', 'main:case-detail', slug='mid-term-rental-crm')
        self.assertContains(response, f'<a class="text-link" href="{crm}">Ver un ejemplo real')

    def test_offers_linkedin_and_github(self):
        response = self.get_home('en')

        self.assertContains(response, f'href="{settings.OWNER_LINKEDIN_URL}"')
        self.assertContains(response, f'href="{settings.OWNER_GITHUB_URL}"')

    def test_shows_no_placeholder_text(self):
        for language in ['en', 'es']:
            with self.subTest(language=language):
                text = visible_text(self.get_home(language))

                self.assertNotRegex(text, r'\[[A-ZÁÉÍÓÚÑ ]{4,}')
                self.assertNotIn('PENDIENTE', text)
                self.assertNotIn('PENDING', text)


class HomeBlogTests(TestCase):
    """
    The home's "From the blog": the three latest posts while the latest is less than a year old, and nothing at all
    while there are none or the blog has gone quiet.
    """

    def test_a_fresh_blog_is_shown(self):
        create_post('Recent', days_ago=364)

        response = self.client.get(reverse_in('en', 'main:index'))

        self.assertContains(response, 'id="blog"')
        self.assertContains(response, 'From the blog')

    def test_a_blog_quiet_for_over_a_year_is_not_shown(self):
        create_post('A quiet post', days_ago=366)
        create_post('An older post', days_ago=500)

        response = self.client.get(reverse_in('es', 'main:index'))

        self.assertNotContains(response, 'id="blog"')
        self.assertNotContains(response, 'Del blog')
        self.assertNotContains(response, 'A quiet post')

    def test_the_latest_post_decides_and_brings_the_older_ones(self):
        create_post('New', days_ago=10)
        create_post('Old', days_ago=800)

        rows = inner_html(self.client.get(reverse_in('en', 'main:index')), 'post-rows')

        self.assertEqual(re.findall(r'<span>([^<]+)</span>', rows), ['New', 'Old'])

    def test_without_posts_the_home_has_no_blog_section(self):
        create_post('Draft', is_published=False)

        response = self.client.get(reverse_in('en', 'main:index'))

        self.assertNotContains(response, 'id="blog"')
        self.assertNotContains(response, 'From the blog')

    def test_lists_the_three_latest_posts(self):
        for number in range(5):
            create_post(f'Post {number}', days_ago=number)

        response = self.client.get(reverse_in('es', 'main:index'))

        rows = inner_html(response, 'post-rows')
        self.assertEqual(re.findall(r'<span>([^<]+)</span>', rows), ['Post 0', 'Post 1', 'Post 2'])
        self.assertIn(f'href="{reverse_in("es", "blog:post-detail", slug="post-0")}"', rows)
        self.assertContains(response, f'<a class="blog-teaser__all" href="{reverse_in("es", "blog:post-list")}">')


class HomeWithoutPostsTests(TestCase):
    """The list of posts moved from the home to the blog (blog:post-list)."""

    def test_the_home_no_longer_lists_the_posts_or_loads_htmx(self):
        for number in range(POSTS_PAGE_SIZE + 1):
            create_post(f'Post {number}', days_ago=number)

        response = self.client.get(reverse_in('en', 'main:index'))

        self.assertNotContains(response, 'grid__post')
        self.assertNotContains(response, 'load-more-posts')
        # The script itself: a case may well mention htmx in its text
        self.assertNotContains(response, static('js/htmx-2.0.11.min.js'))

    def test_the_homes_old_pages_of_posts_redirect_to_the_blogs(self):
        response = self.client.get(reverse_in('es', 'main:index'), {'page': 2, 'utm_source': 'x'})

        self.assertRedirects(
            response,
            f'{reverse_in("es", "blog:post-list")}?page=2&utm_source=x',
            status_code=301,
            fetch_redirect_response=False,
        )

    def test_the_old_load_more_address_redirects_to_the_blogs(self):
        response = self.client.get('/en/more-posts/', {'page': 2})

        self.assertRedirects(
            response, f'{reverse_in("en", "blog:more-posts")}?page=2', status_code=301, fetch_redirect_response=False
        )


class FewPostsTests(TestCase):
    """While every post fits on the blog's first page, the sidebar's list would only repeat them, so it waits."""

    def get_pages(self, posts):
        for number in range(posts):
            create_post(f'Post {number}', days_ago=number, category=create_category(f'topic-{number}'))
        blog = self.client.get(reverse_in('en', 'blog:post-list'))
        post = self.client.get(reverse_in('en', 'blog:post-detail', slug='post-0'))
        return blog, post

    def test_the_sidebars_latest_posts_wait_for_more_posts(self):
        for page in self.get_pages(POSTS_PAGE_SIZE):
            self.assertNotContains(page, 'widget-featured-posts')
            # The footer keeps its own list
            self.assertContains(page, '<h3 class="footer__title">Recent Posts</h3>')

    def test_they_show_up_with_one_post_more(self):
        for page in self.get_pages(POSTS_PAGE_SIZE + 1):
            self.assertContains(page, 'widget-featured-posts')


class SiteLayoutTests(TestCase):
    """The main site has its own layout and stylesheet (templates/site.html); the blog keeps the theme's."""

    def test_main_site_pages_load_the_sites_stylesheet_not_the_themes(self):
        for name in MAIN_SITE_PAGES:
            with self.subTest(page=name):
                response = self.client.get(reverse_in('en', name))

                self.assertIn(static('css/site.css'), stylesheets(response))
                self.assertNotIn(static('css/main.css'), stylesheets(response))
                self.assertNotIn(static('css/brand.css'), stylesheets(response))
                # The theme's script needs the theme's markup
                self.assertNotIn(static('js/common.js'), scripts(response))
                self.assertIn(static('js/site.js'), scripts(response))

    def test_case_pages_load_the_sites_stylesheet(self):
        response = self.client.get(reverse_in('en', 'main:case-detail', slug='this-site'))

        self.assertIn(static('css/site.css'), stylesheets(response))
        self.assertNotIn(static('css/main.css'), stylesheets(response))

    def test_the_blog_keeps_the_themes_stylesheet(self):
        post = create_post('A post')
        for url in [reverse_in('en', 'blog:post-list'), reverse_in('en', 'blog:post-detail', slug=post.slug)]:
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertIn(static('css/main.css'), stylesheets(response))
                self.assertNotIn(static('css/site.css'), stylesheets(response))

    def test_every_stylesheet_and_script_is_a_file_of_the_site(self):
        for name in MAIN_SITE_PAGES:
            response = self.client.get(reverse_in('en', name))
            for url in stylesheets(response) + scripts(response):
                with self.subTest(page=name, url=url):
                    self.assertIsNotNone(finders.find(url.removeprefix(settings.STATIC_URL)))

    def test_new_pages_have_no_style_attributes(self):
        pages = [reverse_in('en', name) for name in MAIN_SITE_PAGES]
        pages += [reverse_in('es', 'main:case-detail', slug=case.slug) for case in cases.visible_cases()]
        for url in pages:
            with self.subTest(url=url):
                self.assertNotContains(self.client.get(url), 'style=')

    def test_one_h1_and_no_skipped_heading_levels(self):
        create_post('A post')
        pages = [reverse_in('en', name) for name in MAIN_SITE_PAGES]
        pages += [reverse_in('en', 'main:case-detail', slug=case.slug) for case in cases.visible_cases()]
        for url in pages:
            with self.subTest(url=url):
                levels = headings(self.client.get(url))

                self.assertEqual(levels[0], 1)
                self.assertEqual(levels.count(1), 1)
                for previous, level in itertools.pairwise(levels):
                    self.assertLessEqual(level, previous + 1)

    def test_arrows_are_decoration_screen_readers_skip(self):
        for url in [reverse_in('en', 'main:index'), reverse_in('en', 'main:case-detail', slug='this-site')]:
            with self.subTest(url=url):
                content = self.client.get(url).content.decode()

                arrows = content.count('→') + content.count('↗')
                hidden = len(re.findall(r'<span class="arrow" aria-hidden="true">[→↗]</span>', content))
                self.assertGreater(arrows, 0)
                self.assertEqual(arrows, hidden)

    def test_texts_use_no_em_dashes(self):
        pages = [reverse_in(language, 'main:index') for language in ['en', 'es']]
        pages += [reverse_in('es', 'main:case-detail', slug=case.slug) for case in cases.visible_cases()]
        for url in pages:
            with self.subTest(url=url):
                self.assertNotIn('—', visible_text(self.client.get(url)))

    def test_dark_is_the_default_theme(self):
        response = self.client.get(reverse_in('en', 'main:index'))

        self.assertContains(response, '<html lang="en" dark="" class="dark-mode">')
        self.assertIn(static('js/theme.js'), scripts(response))

    def test_the_tokens_have_a_dark_and_a_light_value(self):
        styles = Path(finders.find('css/site.css')).read_text(encoding='utf-8')
        light = re.search(r'^:root \{(.*?)\}', styles, re.MULTILINE | re.DOTALL).group(1)
        dark = re.search(r'^\[dark\]:root \{(.*?)\}', styles, re.MULTILINE | re.DOTALL).group(1)

        for token in ['--bg', '--bg-alt', '--text', '--text-2', '--muted', '--line', '--btn-bg', '--btn-text']:
            with self.subTest(token=token):
                self.assertIn(f'{token}:', light)
                self.assertIn(f'{token}:', dark)


class BrandTests(TestCase):
    wordmark = '<span class="brand-wordmark"><span class="brand-wordmark__prefix" aria-hidden="true">~/</span>bracho'

    def test_header_and_footer_show_the_wordmark(self):
        for url in [reverse('main:index'), reverse('blog:post-list')]:
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), self.wordmark, count=2)

    def test_logo_link_has_a_name_in_each_language(self):
        spanish = self.client.get(reverse_in('es', 'main:index'))
        english = self.client.get(reverse_in('en', 'main:index'))

        self.assertContains(spanish, 'aria-label="Bracho, inicio"')
        self.assertContains(english, 'aria-label="Bracho, home"')

    def test_the_footer_ends_with_the_accent_strip(self):
        response = self.client.get(reverse_in('en', 'main:index'))

        self.assertContains(response, '<div class="site-footer__accent" aria-hidden="true"></div>')

    def test_the_footer_links_to_the_secondary_pages(self):
        for language in ['en', 'es']:
            with self.subTest(language=language):
                footer = inner_html(self.client.get(reverse_in(language, 'main:index')), 'site-footer__nav')

                for url in [
                    f'{reverse_in(language, "main:index")}#cases',
                    reverse_in(language, 'blog:post-list'),
                    reverse_in(language, 'main:cv'),
                    reverse_in(language, 'main:about'),
                    reverse_in(language, 'main:privacy'),
                ]:
                    self.assertIn(f'href="{url}"', footer)


class SiteHeaderTests(TestCase):
    """The main site's header: its links, the language switch and the theme toggle."""

    def test_links_to_the_cases_how_i_work_the_blog_the_cv_and_contact(self):
        for language in ['en', 'es']:
            with self.subTest(language=language):
                header = inner_html(self.client.get(reverse_in(language, 'main:about')), 'site-nav')
                home = reverse_in(language, 'main:index')

                for url in [
                    f'{home}#cases',
                    f'{home}#how-i-work',
                    reverse_in(language, 'blog:post-list'),
                    reverse_in(language, 'main:cv'),
                    reverse_in(language, 'main:contact'),
                ]:
                    self.assertIn(f'href="{url}"', header)

    def test_marks_the_current_page(self):
        response = self.client.get(reverse_in('en', 'main:cv'))

        self.assertContains(response, f'href="{reverse_in("en", "main:cv")}" aria-current="page"')

    def test_the_language_switch_is_a_form_that_needs_no_javascript(self):
        for language, other, name in [('en', 'es', 'Switch to Spanish'), ('es', 'en', 'Cambiar a inglés')]:
            with self.subTest(language=language):
                page = self.client.get(reverse_in(language, 'main:cv'))

                self.assertContains(page, f'action="{reverse_in(language, "set_language")}" method="post"')
                self.assertContains(
                    page, f'<input type="hidden" name="next" value="{reverse_in(language, "main:cv")}">'
                )
                self.assertContains(page, f'type="submit" name="language" value="{other}" aria-label="{name}"')

    def test_language_switch_opens_the_same_page_in_the_other_language(self):
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

    def test_the_theme_toggle_is_a_button_hidden_until_its_script_runs(self):
        response = self.client.get(reverse_in('es', 'main:index'))

        self.assertRegex(
            response.content.decode(),
            r'<button class="site-nav__control site-theme" type="button" hidden\s+'
            r'data-label-light="Tema claro" data-label-dark="Tema oscuro">',
        )
        self.assertIn('toggle.hidden = false', Path(finders.find('js/site.js')).read_text(encoding='utf-8'))


class BlogHeaderTests(TestCase):
    """The blog keeps the theme's header: its controls are buttons, so they work with a keyboard."""

    def get_blog(self, language):
        return self.client.get(reverse_in(language, 'blog:post-list'))

    def test_controls_are_buttons(self):
        response = self.get_blog('en')

        for control in ['hamburger', 'toggle-theme', 'dropdown-toggle', 'search-button', 'search__close']:
            self.assertContains(response, f'<button type="button" class="{control}"')

    def test_controls_are_named_in_each_language(self):
        response = self.get_blog('es')

        self.assertContains(response, 'aria-label="Menú"')
        self.assertContains(response, 'aria-label="Modo oscuro"')
        self.assertContains(response, '<span class="screen-reader-text">Idioma:</span>')
        self.assertContains(response, 'aria-label="Cerrar búsqueda"')
        self.assertContains(response, 'placeholder="Escribe para buscar..."')

    def test_language_menu_is_a_form_that_needs_no_javascript(self):
        page = self.get_blog('en')

        self.assertContains(page, f'<form action="{reverse_in("en", "set_language")}" method="post"')
        self.assertContains(page, '<button type="submit" name="language" value="es"')

    def test_links_to_the_cases(self):
        for language, name in [('en', 'Cases'), ('es', 'Casos')]:
            with self.subTest(language=language):
                cases_url = f'{reverse_in(language, "main:index")}#cases'

                self.assertContains(self.get_blog(language), f'<a href="{cases_url}" class="nav__link">{name}</a>')


class PageAccessibilityTests(TestCase):
    """Both layouts work with a keyboard, and screen readers hear them in the page's language."""

    def test_back_to_top_is_a_button_named_in_each_language(self):
        for language, name in [('en', 'Back to top'), ('es', 'Volver arriba')]:
            with self.subTest(language=language):
                response = self.client.get(reverse_in(language, 'blog:post-list'))

                self.assertContains(response, f'<button type="button" class="top" aria-label="{name}"')

    def test_enlarged_post_images_open_in_a_dialog_named_in_each_language(self):
        post = create_post('With images')

        for language, dialog, button in [
            ('en', 'Enlarged image', 'Enlarge image'),
            ('es', 'Imagen ampliada', 'Ampliar imagen'),
        ]:
            with self.subTest(language=language):
                response = self.client.get(reverse_in(language, 'blog:post-detail', slug=post.slug))

                # static/js/common.js names each image with data-enlarge-label and focuses the dialog
                self.assertContains(
                    response, f'<div class="images-overlay" role="dialog" aria-modal="true" aria-label="{dialog}"'
                )
                self.assertContains(response, f'tabindex="-1" data-enlarge-label="{button}"')

    def test_the_only_main_landmark_needs_no_label(self):
        site = self.client.get(reverse_in('es', 'main:index'))
        blog = self.client.get(reverse_in('es', 'blog:post-list'))

        self.assertContains(site, '<main', count=1)
        self.assertContains(site, '<main class="site-main" id="content" tabindex="-1">')
        self.assertContains(blog, '<main', count=1)
        self.assertContains(blog, '<main class="content" id="content" tabindex="-1">')

    def test_a_skip_link_leads_past_the_header_in_each_language(self):
        for language, name in [('en', 'Skip to content'), ('es', 'Saltar al contenido')]:
            for page in ['main:index', 'blog:post-list']:
                with self.subTest(language=language, page=page):
                    response = self.client.get(reverse_in(language, page))
                    body = re.split(r'<body[^>]*>', response.content.decode(), maxsplit=1)[1]

                    # The first link in the page, so the first thing the keyboard reaches
                    first_link = re.search(r'<a [^>]*>[^<]*</a>', body).group(0)
                    self.assertEqual(first_link, f'<a class="skip-link" href="#content">{name}</a>')


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
        for stylesheet in ['css/fonts.css', 'css/main.css', 'css/site.css']:
            for url in re.findall(r'url\(([^)]+)\)', Path(finders.find(stylesheet)).read_text()):
                with self.subTest(stylesheet=stylesheet, url=url):
                    self.assertIsNotNone(finders.find(posixpath.normpath(posixpath.join('css', url))))

    def test_preloaded_fonts_are_ones_the_stylesheet_uses(self):
        fonts_css = Path(finders.find('css/fonts.css')).read_text()

        # Each layout preloads the Poppins weight its first screen uses: the main site's body text, the blog's headings
        for page, poppins in [
            ('main:index', 'poppins-400'),
            ('main:contact', 'poppins-400'),
            ('blog:post-list', 'poppins-700'),
        ]:
            response = self.client.get(reverse(page))
            preloads = re.findall(r'<link rel="preload" href="([^"]+)" as="font"', response.content.decode())

            self.assertEqual(len(preloads), 2)
            self.assertIn(poppins, preloads[1])
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
    def test_pages_recruiters_land_on_show_the_name_and_role(self):
        image_url = f'http://testserver{static("images/og-profile.png")}'

        for name in ['main:index', 'main:cv']:
            for language in ['en', 'es']:
                with self.subTest(page=name, language=language):
                    response = self.client.get(reverse_in(language, name))

                    self.assertEqual(meta(response, 'og:image'), image_url)
                    self.assertEqual(meta(response, 'twitter:image'), image_url)
                    self.assertEqual(meta(response, 'og:image:width'), '1200')
                    self.assertEqual(meta(response, 'og:image:height'), '630')

    def test_the_profile_image_is_a_file_of_the_site_in_the_preview_size(self):
        image = Path(finders.find('images/og-profile.png')).read_bytes()

        # A PNG's width and height are the first two numbers of its IHDR chunk
        self.assertEqual((int.from_bytes(image[16:20]), int.from_bytes(image[20:24])), SOCIAL_SIZE)

    def test_the_other_pages_use_the_brand_one(self):
        image_url = f'http://testserver{static("images/og-default.png")}'

        # The contact page doesn't extend base.html, so it gets its own check
        for name in ['main:about', 'main:privacy', 'main:contact']:
            with self.subTest(page=name):
                response = self.client.get(reverse_in('en', name))

                self.assertEqual(meta(response, 'og:image'), image_url)
                self.assertEqual(meta(response, 'twitter:image'), image_url)
                self.assertNotContains(response, 'twitter:image:src')


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
                self.assertContains(response, '<h1 class="page__title">Page not found</h1>', status_code=404)
                self.assertContains(response, static('css/site.css'), status_code=404)
                self.assertNotContains(response, static('css/main.css'), status_code=404)
                self.assertContains(response, 'class="site-header"', status_code=404)
                self.assertContains(response, 'class="site-footer"', status_code=404)
                self.assertNotContains(response, 'name="description"', status_code=404)
                self.assertNotContains(response, 'rel="canonical"', status_code=404)
                self.assertNotContains(response, 'hreflang', status_code=404)
                self.assertNotContains(response, 'og:url', status_code=404)

        with self.assertLogs('django.request', 'WARNING'):
            spanish = self.client.get('/es/no-such-page/')
        self.assertContains(spanish, '<title>Página no encontrada - Nestor Bracho</title>', status_code=404)
        self.assertContains(spanish, '<h1 class="page__title">Página no encontrada</h1>', status_code=404)
        self.assertContains(spanish, 'class="site-header"', status_code=404)
        self.assertContains(spanish, 'class="site-footer"', status_code=404)
        self.assertNotContains(spanish, 'rel="canonical"', status_code=404)


class CasesIndexTests(TestCase):
    def test_sends_visitors_to_the_homes_cases(self):
        for language in ['en', 'es']:
            with self.subTest(language=language):
                response = self.client.get(f'/{language}/cases/')

                # Temporary: a cases page may come later, and browsers would remember a permanent one
                self.assertRedirects(
                    response,
                    f'{reverse_in(language, "main:index")}#cases',
                    status_code=302,
                    fetch_redirect_response=False,
                )

    def test_case_pages_are_still_found(self):
        response = self.client.get(reverse_in('en', 'main:case-detail', slug='this-site'))

        self.assertEqual(response.status_code, 200)


class OwnerLocationSettingTests(SimpleTestCase):
    """OWNER_LOCATION_ES is the Spanish location; without it, the English one."""

    def locations(self, **environment):
        names = ['OWNER_LOCATION', 'OWNER_LOCATION_ES']
        kept = {name: value for name, value in os.environ.items() if name not in names}
        with mock.patch.dict(os.environ, {**kept, **environment}, clear=True):
            # Without the local .env, which would set them again
            with mock.patch('environ.Env.read_env'):
                return runpy.run_path(str(Path(settings.BASE_DIR) / 'config' / 'settings.py'))['OWNER_LOCATIONS']

    def test_the_spanish_one_when_set(self):
        locations = self.locations(OWNER_LOCATION='Madrid, Spain', OWNER_LOCATION_ES='Madrid, España')

        self.assertEqual(locations, {'en': 'Madrid, Spain', 'es': 'Madrid, España'})

    def test_the_english_one_when_unset(self):
        locations = self.locations(OWNER_LOCATION='Madrid, Spain')

        self.assertEqual(locations, {'en': 'Madrid, Spain', 'es': 'Madrid, Spain'})


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
        self.assertIn('Django', data['knowsAbout'])
        self.assertTrue(data['description'].startswith('Staff Engineer with more than'))
        self.assertIn('now freelance', data['description'])
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

    @override_settings(NEWSLETTER_ENABLED=True)
    def test_is_linked_from_every_form_and_the_sitemap(self):
        privacy_link = f'href="{reverse("main:privacy")}"'

        self.assertContains(self.client.get(reverse('main:contact')), privacy_link)
        # The blog's list has the newsletter form and the footer
        self.assertContains(self.client.get(reverse('blog:post-list')), privacy_link, count=2)
        self.assertContains(self.client.get(reverse('sitemap')), f'http://testserver{reverse("main:privacy")}')

    @override_settings(OWNER_EMAIL='nestor@example.com')
    def test_keeps_the_email_readable_without_javascript(self):
        # Cloudflare's Email Obfuscation leaves alone what is between these comments
        for language in ['en', 'es']:
            with self.subTest(language=language):
                response = self.client.get(reverse_in(language, 'main:privacy'))

                self.assertContains(
                    response,
                    '<!--email_off--><a href="mailto:nestor@example.com">nestor@example.com</a><!--/email_off-->',
                )


class NewsletterTests(TestCase):
    """Nothing sends the newsletter yet: until NEWSLETTER_ENABLED, the site neither offers it nor promises it."""

    @override_settings(NEWSLETTER_ENABLED=False)
    def test_is_neither_offered_nor_in_the_privacy_policy_while_off(self):
        for language in ['en', 'es']:
            with self.subTest(language=language):
                home = self.client.get(reverse_in(language, 'main:index'))
                privacy = self.client.get(reverse_in(language, 'main:privacy'))

                self.assertNotContains(home, 'widget-subscribe')
                self.assertNotContains(home, reverse('usermanager:newsletter-subscriber'))
                self.assertNotContains(privacy, 'widget-subscribe')
                self.assertNotContains(privacy, 'newsletter')

    @override_settings(NEWSLETTER_ENABLED=True)
    def test_is_offered_and_explained_while_on(self):
        for language in ['en', 'es']:
            with self.subTest(language=language):
                blog = self.client.get(reverse_in(language, 'blog:post-list'))
                privacy = self.client.get(reverse_in(language, 'main:privacy'))

                self.assertContains(blog, f'action="{reverse("usermanager:newsletter-subscriber")}')
                self.assertContains(privacy, '<strong>Newsletter:</strong>')

    def test_is_off_unless_the_environment_turns_it_on(self):
        self.assertFalse(settings.NEWSLETTER_ENABLED)


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

    def test_describes_the_page_in_a_search_result_with_the_role(self):
        for language in ['en', 'es']:
            with self.subTest(language=language):
                description = meta(self.client.get(reverse_in(language, 'main:about')), 'description')

                # Search engines cut descriptions at about 160 characters
                self.assertLessEqual(len(description), 160)
                self.assertIn(settings.OWNER_ROLE, description)

    def test_the_largest_image_is_not_lazy_loaded(self):
        response = self.client.get(reverse_in('en', 'main:about'))

        image = re.search(r'<img [^>]*images/02\.jpg[^>]*>', response.content.decode()).group(0)
        self.assertIn('fetchpriority="high"', image)
        self.assertNotIn('lazy', image)

    def test_spanish_title_is_spelled_right(self):
        response = self.client.get(reverse_in('es', 'main:about'))

        self.assertContains(response, '<title>Sobre mí - Nestor Bracho</title>')

    def test_gives_the_current_role(self):
        english = self.client.get(reverse_in('en', 'main:about'))
        spanish = self.client.get(reverse_in('es', 'main:about'))

        self.assertContains(english, 'a Senior Software Engineer by trade')
        self.assertContains(spanish, 'Senior Software Engineer de profesión')
        self.assertNotContains(english, 'fullstack developer by trade')
        self.assertNotContains(spanish, 'desarrollador fullstack de profesión')

    def test_headings_have_no_emojis(self):
        for language in ['en', 'es']:
            with self.subTest(language=language):
                content = self.client.get(reverse_in(language, 'main:about')).content.decode()

                for heading in re.findall(r'<h2[^>]*>(.*?)</h2>', content):
                    self.assertRegex(heading, r'^[\w¿¡]')


@override_settings(OWNER_CV_PDF_URLS={'en': '/media/cv/cv-en.pdf', 'es': '/media/cv/cv-es.pdf'})
class CVViewTests(TestCase):
    def test_shows_the_whole_cv_in_each_language(self):
        spanish = self.client.get(reverse_in('es', 'main:cv'))
        english = self.client.get(reverse_in('en', 'main:cv'))

        self.assertContains(spanish, 'Experiencia profesional')
        self.assertNotContains(spanish, 'Professional experience')
        self.assertContains(english, 'Professional experience')

    def test_has_every_section_of_docs_cv_content(self):
        sections = {
            'en': [
                'Summary',
                'Generative AI and agents',
                'Professional experience',
                'Technical skills',
                'Certifications',
                'Education',
                'Languages',
            ],
            'es': [
                'Perfil',
                'IA generativa y agentes',
                'Experiencia profesional',
                'Habilidades técnicas',
                'Certificaciones',
                'Formación',
                'Idiomas',
            ],
        }
        for language, titles in sections.items():
            with self.subTest(language=language):
                response = self.client.get(reverse_in(language, 'main:cv'))

                self.assertEqual(re.findall(r'<h2>([^<]+)</h2>', response.content.decode()), titles)

    def test_leads_with_the_freelance_work_and_its_projects(self):
        for language, job, projects in [
            (
                'en',
                '<strong>Freelance</strong> · Madrid · Jun 2026 – Present',
                ['Management platform and CRM for a vacation', 'Warehouse management system for a logistics company'],
            ),
            (
                'es',
                '<strong>Freelance</strong> · Madrid · jun 2026 – actualidad',
                ['Plataforma de gestión y CRM para una gestora', 'Sistema de gestión de almacén para una empresa'],
            ),
        ]:
            with self.subTest(language=language):
                content = self.client.get(reverse_in(language, 'main:cv')).content.decode()
                first_job = content.split('<section class="cv__job">')[1]

                self.assertIn(job, first_job)
                self.assertEqual(len(re.findall(r'<h4 class="cv__project">', first_job)), 2)
                for project in projects:
                    self.assertIn(project, first_job)

    def test_headline_adds_ai_agent_driven_development(self):
        for language, headline in [
            ('en', f'{settings.OWNER_ROLE} · Python/Django · AI agent-driven development'),
            ('es', f'{settings.OWNER_ROLE} · Python/Django · Desarrollo con agentes de IA'),
        ]:
            with self.subTest(language=language):
                response = self.client.get(reverse_in(language, 'main:cv'))

                self.assertEqual(html.unescape(inner_html(response, 'cv__headline')), headline)

    def test_gives_the_english_level(self):
        english = self.client.get(reverse_in('en', 'main:cv'))
        spanish = self.client.get(reverse_in('es', 'main:cv'))

        self.assertContains(english, 'Spanish (native) · English (B2, upper intermediate)')
        self.assertContains(spanish, 'Español (nativo) · Inglés (B2, intermedio alto)')

    def test_title_leads_with_the_name_and_role(self):
        for language in ['en', 'es']:
            with self.subTest(language=language):
                response = self.client.get(reverse_in(language, 'main:cv'))

                self.assertEqual(page_title(response), f'CV · Nestor Bracho, {settings.OWNER_ROLE}')
                self.assertEqual(meta(response, 'og:title'), page_title(response))
                self.assertEqual(meta(response, 'twitter:title'), page_title(response))

    def test_explains_the_jobs_that_overlap(self):
        # Freelance work ran alongside other jobs: each one says so next to its dates, or they read like a mistake
        jobs = {
            'en': [
                (
                    '<strong>World Bank Group</strong> · Contract · Madrid, remote · Jun 2023 – Jun 2026',
                    'Alongside my role at Selia until Sep 2023 and Ekwi-three in 2024.',
                ),
                (
                    '<strong>Ekwi-three GmbH</strong> · Freelance · Remote · May 2024 – Dec 2024',
                    'Alongside my contract with the World Bank Group.',
                ),
                (
                    '<strong>Selia</strong> · Full-time · Remote · Jan 2022 – Sep 2023',
                    'From Dec 2022, alongside my projects for the World Bank Group.',
                ),
                (
                    '<strong>World Bank Group</strong> · Freelance · Remote · Dec 2022 – Mar 2023',
                    'Alongside my full-time role at Selia.',
                ),
            ],
            'es': [
                (
                    '<strong>Grupo Banco Mundial</strong> · Contrato · Madrid, remoto · jun 2023 – jun 2026',
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

    @override_settings(
        OWNER_EMAIL='nestor@example.com', OWNER_LOCATIONS={'en': 'Madrid, Spain', 'es': 'Madrid, España'}
    )
    def test_gives_the_contact_details_when_configured(self):
        english = self.client.get(reverse_in('en', 'main:cv'))
        spanish = self.client.get(reverse_in('es', 'main:cv'))

        self.assertContains(english, 'href="mailto:nestor@example.com"')
        self.assertContains(english, '<li>Madrid, Spain</li>')
        self.assertContains(spanish, '<li>Madrid, España</li>')

    @override_settings(OWNER_EMAIL='nestor@example.com')
    def test_keeps_the_email_readable_for_cv_parsers(self):
        # Cloudflare's Email Obfuscation would swap it for a link to a script; it leaves alone what is between these
        response = self.client.get(reverse_in('en', 'main:cv'))

        self.assertContains(
            response, '<!--email_off--><a href="mailto:nestor@example.com">nestor@example.com</a><!--/email_off-->'
        )

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
        home = self.client.get(reverse('main:index'))
        blog = self.client.get(reverse('blog:post-list'))

        # The home's hero links each profile that is set; the blog's footer and sidebar both render the list
        self.assertContains(home, 'href="https://github.com/example"', count=1)
        self.assertContains(blog, 'href="https://github.com/example"', count=2)
        self.assertNotContains(home, 'fa-linkedin"')
        self.assertNotContains(blog, 'fa-linkedin"')

    @override_settings(OWNER_LINKEDIN_URL='https://www.linkedin.com/in/example')
    def test_links_linkedin_when_configured(self):
        home = self.client.get(reverse('main:index'))
        blog = self.client.get(reverse('blog:post-list'))

        # The home's hero; the blog's footer and sidebar
        self.assertContains(home, 'href="https://www.linkedin.com/in/example"', count=1)
        self.assertContains(blog, 'href="https://www.linkedin.com/in/example"', count=2)


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

    def test_the_home_confirms_the_request_was_sent(self):
        response = self.client.post(reverse_in('en', 'main:contact'), self.data, follow=True)

        self.assertContains(
            response,
            '<p class="site-message site-message--success" role="status">Your contact request has been successfully '
            'submitted. I&#x27;ll get in touch as soon as possible!</p>',
        )

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


def make_case(slug, **overrides):
    """A complete, published case for the tests; any field can be overridden."""
    values = {
        'group': cases.OTHER,
        'layout': cases.NORMAL,
        'published': True,
        'title': cases.Text(f'{slug} title', f'{slug} título'),
        'summary': cases.Text(f'{slug} summary', f'{slug} resumen'),
        'proof_line': cases.Text('Django · 10 tests'),
        'authorship': cases.Text('Sole author', 'Autor único'),
        'card_meta': cases.Text('Example Org · 2024', 'Organización de ejemplo · 2024'),
        'client': cases.Text('Example Org', 'Organización de ejemplo'),
        'period': cases.Text('2024'),
        'role': cases.Text('Architecture', 'Arquitectura'),
        'problem': cases.Text(f'{slug} problem', f'{slug} problema'),
        'solution': (cases.Text('First point', 'Primer punto'), cases.Text('Second point', 'Segundo punto')),
        'how_built': cases.Text('With agents', 'Con agentes'),
        'result': cases.Text('It works', 'Funciona'),
        'stack': ('Python', 'Django'),
        'links': (cases.Link('GitHub', 'https://github.com/example/case'),),
        'screenshot': None,
        **overrides,
    }
    return cases.Case(slug=slug, **values)


def case_labels(response):
    """The labels of a case page's blocks, as "01 / The problem"."""
    return re.findall(r'<h2 class="case-block__label">.*?</span>([^<]+)</h2>', response.content.decode())


def card_titles(response):
    return re.findall(r'<h3 class="case-card__title">([^<]+)</h3>', response.content.decode())


# The real cases' slugs that are still drafts (docs/home-cases.md): their problem or their content is pending
DRAFT_SLUGS = ['payments-and-b2b', 'warehouse-management-system']


def case_by_slug(slug):
    """A case as main/cases.py writes it, drafts included."""
    return next(case for case in cases.CASES if case.slug == slug)


class CaseContentTests(SimpleTestCase):
    """The cases in main/cases.py, as written from docs/home-cases.md."""

    def test_slugs_are_unique_and_valid(self):
        slugs = [case.slug for case in cases.CASES]

        self.assertEqual(len(slugs), len(set(slugs)))
        for slug in slugs:
            self.assertRegex(slug, r'^[a-z0-9]+(-[a-z0-9]+)*$')

    def test_the_seven_cases_in_their_groups_and_order(self):
        self.assertEqual(
            [(case.slug, case.group, case.layout) for case in cases.CASES],
            [
                ('local-development-portal', cases.WORLD_BANK, cases.WIDE),
                ('participatory-monitoring-app', cases.WORLD_BANK, cases.NORMAL),
                ('e3-django-dynamic-forms', cases.WORLD_BANK, cases.NORMAL),
                ('mid-term-rental-crm', cases.OTHER, cases.WIDE),
                ('payments-and-b2b', cases.OTHER, cases.NORMAL),
                ('warehouse-management-system', cases.OTHER, cases.NORMAL),
                ('this-site', cases.OTHER, cases.NORMAL),
            ],
        )

    def test_the_mobile_apps_period(self):
        case = case_by_slug('participatory-monitoring-app')

        self.assertEqual(case.period, cases.Text('2026'))

    def test_the_crm_names_the_llm_service_and_its_api(self):
        case = case_by_slug('mid-term-rental-crm')

        self.assertEqual(len(case.solution), 8)
        self.assertTrue(case.solution[7].en.startswith('On the same platform, before the CRM, I built a financial'))
        self.assertTrue(case.solution[7].es.startswith('En la misma plataforma, antes del CRM, construí un servicio'))
        self.assertEqual(case.stack.index('OpenAI API') + 1, case.stack.index('GitHub Actions'))

    def test_the_warehouse_case_holds_what_is_written_and_stays_a_draft(self):
        case = case_by_slug('warehouse-management-system')

        self.assertEqual(case.card_meta, cases.Text('Logistics company · 2026', 'Empresa de logística · 2026'))
        self.assertEqual(len(case.solution), 1)
        self.assertEqual(case.stack, ('Python', 'Django', 'HTMX', 'PostgreSQL', 'Celery', 'AWS', 'Terraform'))
        self.assertFalse(case.published)
        self.assertFalse(case.is_published())

    def test_five_are_published_and_the_drafts_are_not(self):
        published = [case.slug for case in cases.CASES if case.is_published()]

        self.assertEqual(len(published), 5)
        for slug in DRAFT_SLUGS:
            self.assertNotIn(slug, published)

    def test_a_case_is_published_only_when_marked_and_complete(self):
        self.assertTrue(make_case('done').is_published())
        self.assertFalse(make_case('not-marked', published=False).is_published())
        for field, empty in [('summary', None), ('problem', None), ('solution', ())]:
            with self.subTest(missing=field):
                self.assertFalse(make_case('incomplete', **{field: empty}).is_published())
        # The optional ones
        self.assertTrue(make_case('bare', how_built=None, result=None, links=(), authorship=None).is_published())

    def test_no_pending_marker_is_loaded(self):
        for case in cases.CASES:
            for name, value in case.texts():
                with self.subTest(case=case.slug, field=name):
                    for text in [value.en, value.es or '']:
                        self.assertNotIn('PENDIENTE', text)
                        self.assertNotIn('PENDING', text)
                        self.assertNotIn('[', text)

    def test_texts_use_no_em_dashes(self):
        for case in cases.CASES:
            for name, value in case.texts():
                with self.subTest(case=case.slug, field=name):
                    self.assertNotIn('—', value.en)
                    self.assertNotIn('—', value.es or '')

    def test_prose_is_written_in_both_languages(self):
        # Without its Spanish, a text would show in English on the Spanish page without anyone noticing. Names,
        # periods, stacks, proof lines and links may be written once.
        prose = {'summary', 'role', 'problem', 'solution', 'how_built', 'result', 'authorship'}
        for case in cases.CASES:
            for name, value in case.texts():
                if name in prose:
                    with self.subTest(case=case.slug, field=name):
                        self.assertTrue(value.es)

    def test_links_are_absolute_https_addresses(self):
        for case in cases.CASES:
            for link in case.links:
                with self.subTest(case=case.slug, link=link.label):
                    self.assertTrue(link.url.startswith('https://'))

    def test_every_case_has_a_known_group_and_layout(self):
        # A typo would drop the case from the home, or show a wide case as a normal card
        for case in cases.CASES:
            with self.subTest(case=case.slug):
                self.assertIn(case.group, cases.GROUPS)
                self.assertIn(case.layout, [cases.WIDE, cases.NORMAL])

    def test_texts_the_same_in_both_languages_are_written_once(self):
        name = cases.Text('Selia')

        self.assertEqual(name.in_language('en'), 'Selia')
        self.assertEqual(name.in_language('es'), 'Selia')


class RealCasesTests(TestCase):
    """The cases in main/cases.py, as production and development show them."""

    def test_production_home_shows_the_five_published_cards_in_two_groups_wide_first(self):
        response = self.client.get(reverse_in('en', 'main:index'))

        self.assertEqual(
            card_titles(response),
            [
                'Local development portal for community-driven programs',
                'Offline-first mobile app for participatory monitoring',
                'e3-django-dynamic-forms',
                'CRM for mid-term rentals, from spec to production',
                'This site',
            ],
        )
        self.assertEqual(
            re.findall(r'<p class="group-label">([^<]+)</p>', response.content.decode()),
            ['World Bank Group · 2023 to 2026', 'Other clients and projects'],
        )
        self.assertContains(response, 'class="case-card case-card--wide"', count=2)
        self.assertNotContains(response, 'dev-mark')

    @override_settings(DEBUG=True)
    def test_development_home_shows_all_seven_and_marks_the_drafts(self):
        response = self.client.get(reverse_in('es', 'main:index'))

        self.assertEqual(len(card_titles(response)), 7)
        self.assertContains(response, '<p class="dev-mark">Solo en desarrollo: no publicado</p>', count=2)

    def test_draft_cases_are_not_found_and_not_in_the_sitemap(self):
        sitemap = self.client.get(reverse('sitemap'))

        for slug in DRAFT_SLUGS:
            with self.subTest(slug=slug):
                with self.assertLogs('django.request', 'WARNING'):
                    response = self.client.get(reverse_in('en', 'main:case-detail', slug=slug))

                self.assertEqual(response.status_code, 404)
                self.assertNotContains(sitemap, slug)

    def test_published_cases_are_in_the_sitemap_in_both_languages(self):
        sitemap = self.client.get(reverse('sitemap'))

        for case in cases.CASES:
            if case.is_published():
                for language in ['en', 'es']:
                    with self.subTest(case=case.slug, language=language):
                        url = reverse_in(language, 'main:case-detail', slug=case.slug)
                        self.assertContains(sitemap, f'<loc>http://testserver{url}</loc>')

    def test_every_published_case_renders_in_both_languages_without_placeholders(self):
        for case in cases.CASES:
            if case.is_published():
                for language in ['en', 'es']:
                    with self.subTest(case=case.slug, language=language):
                        response = self.client.get(reverse_in(language, 'main:case-detail', slug=case.slug))
                        text = visible_text(response)

                        self.assertContains(response, f'<html lang="{language}"')
                        self.assertNotIn('PENDIENTE', text)
                        self.assertNotIn('PENDING', text)
                        self.assertNotRegex(text, r'\[[A-ZÁÉÍÓÚÑ ]{4,}')

    @override_settings(DEBUG=True)
    def test_every_case_renders_in_development_in_both_languages(self):
        for case in cases.CASES:
            for language in ['en', 'es']:
                with self.subTest(case=case.slug, language=language):
                    response = self.client.get(reverse_in(language, 'main:case-detail', slug=case.slug))

                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, f'<html lang="{language}"')

    def test_the_portal_page_matches_the_reference(self):
        response = self.client.get(reverse_in('es', 'main:case-detail', slug='local-development-portal'))

        self.assertContains(response, '<span aria-current="page">local-development-portal</span>')
        self.assertContains(response, '<h1 class="case-hero__title" id="case-title">Portal de desarrollo local')
        self.assertEqual(
            case_labels(response), ['01 / El problema', '02 / Lo que construí', '03 / Stack', '04 / Resultado']
        )
        self.assertContains(response, '<dt>cliente</dt><dd>Grupo Banco Mundial</dd>')
        self.assertContains(response, '<dt>autoría</dt><dd>Equipo</dd>')


@mock.patch(
    'main.cases.CASES',
    [
        make_case('first-case', layout=cases.WIDE),
        make_case('bare-case', how_built=None, result=None, links=(), authorship=None, card_meta=None),
        make_case('drafted-case', published=False),
        make_case(
            'last-case',
            layout=cases.WIDE,
            group=cases.WORLD_BANK,
            screenshot=cases.Screenshot('images/og-default.png', cases.Text('The board', 'El tablero')),
        ),
    ],
)
class CaseDetailTests(TestCase):
    def get_case(self, language, slug='first-case'):
        return self.client.get(reverse_in(language, 'main:case-detail', slug=slug))

    def test_has_its_own_address_in_each_language_with_one_english_slug(self):
        self.assertEqual(reverse_in('en', 'main:case-detail', slug='first-case'), '/en/cases/first-case/')
        self.assertEqual(reverse_in('es', 'main:case-detail', slug='first-case'), '/es/cases/first-case/')

    def test_shows_the_case_in_the_language_of_the_page(self):
        english = self.get_case('en')
        spanish = self.get_case('es')

        self.assertContains(english, 'first-case title')
        self.assertContains(english, 'first-case problem')
        self.assertContains(spanish, 'first-case título')
        self.assertContains(spanish, 'first-case problema')
        self.assertContains(spanish, '<dt>cliente</dt><dd>Organización de ejemplo</dd>')
        self.assertContains(spanish, 'Segundo punto')

    def test_numbers_every_block_the_case_has(self):
        self.assertEqual(
            case_labels(self.get_case('en')),
            [
                '01 / The problem',
                '02 / What I built',
                '03 / How it was built',
                '04 / Stack',
                '05 / Result',
                '06 / Links',
            ],
        )

    def test_leaves_out_the_blocks_the_case_lacks_without_gaps_in_the_numbers(self):
        response = self.get_case('en', 'bare-case')

        self.assertEqual(case_labels(response), ['01 / The problem', '02 / What I built', '03 / Stack'])
        self.assertNotContains(response, '<dt>authorship</dt>')

    def test_the_solution_is_a_numbered_list(self):
        response = self.get_case('en')

        self.assertContains(response, '<ol class="case-block__content case-solution">')
        self.assertContains(
            response, '<li><span class="case-solution__number" aria-hidden="true">02</span><span>Second point</span>'
        )

    def test_a_screenshot_shows_on_the_page_and_the_wide_card_without_a_number(self):
        page = self.get_case('es', 'last-case')
        home = self.client.get(reverse_in('es', 'main:index'))

        image = f'<img src="{static("images/og-default.png")}" alt="El tablero"'
        self.assertContains(page, image)
        self.assertEqual(case_labels(page)[2], '03 / Cómo se construyó')
        self.assertContains(home, '<div class="case-card__shot">')
        self.assertContains(home, image, count=1)

    def test_a_wide_card_without_a_screenshot_leaves_no_empty_slot(self):
        with mock.patch('main.cases.CASES', [make_case('wide-case', layout=cases.WIDE)]):
            response = self.client.get(reverse_in('en', 'main:index'))

        self.assertContains(response, 'class="case-card case-card--wide"')
        self.assertNotContains(response, 'case-card__shot')

    def test_home_groups_the_cases_and_puts_wide_cards_first(self):
        response = self.client.get(reverse_in('en', 'main:index'))

        # The World Bank Group first, whatever the list order; within a group, wide cards first
        self.assertEqual(card_titles(response), ['last-case title', 'first-case title', 'bare-case title'])

    def test_cards_show_what_the_case_has(self):
        response = self.client.get(reverse_in('en', 'main:index'))
        content = response.content.decode()
        first = content[content.index('first-case title') - 600 : content.index('first-case title')]

        self.assertIn('<span class="tag">Sole author</span>', first)
        self.assertIn('<p class="meta">Example Org · 2024</p>', first)
        self.assertContains(response, '<p class="proof-line">Django · 10 tests</p>')
        self.assertContains(response, 'href="https://github.com/example/case" rel="noopener">GitHub')

    def test_next_case_follows_the_list_and_wraps_to_the_first(self):
        first = reverse_in('en', 'main:case-detail', slug='first-case')
        bare = reverse_in('en', 'main:case-detail', slug='bare-case')

        self.assertContains(self.get_case('en'), f'<a class="next-case__link" href="{bare}">')
        # The draft is skipped in production, and the last case leads back to the first
        self.assertContains(self.get_case('en', 'bare-case'), 'href="/en/cases/last-case/"')
        self.assertContains(self.get_case('en', 'last-case'), f'<a class="next-case__link" href="{first}">')

    def test_ends_with_the_contact_call_and_both_buttons(self):
        response = self.get_case('es')

        self.assertContains(response, '¿Tienes un problema parecido? Hablemos.')
        self.assertContains(response, f'<a class="button button--primary" href="{reverse_in("es", "main:contact")}">')
        self.assertContains(response, f'<a class="button" href="{reverse_in("es", "main:cv")}">')

    def test_a_published_case_carries_no_development_mark(self):
        self.assertNotContains(self.get_case('en'), 'dev-mark')

    def test_drafts_are_not_published(self):
        with self.assertLogs('django.request', 'WARNING'):
            response = self.get_case('en', 'drafted-case')

        self.assertEqual(response.status_code, 404)
        self.assertNotContains(self.client.get(reverse_in('en', 'main:index')), 'drafted-case title')

    def test_unknown_cases_are_not_found(self):
        with self.assertLogs('django.request', 'WARNING'):
            self.assertEqual(self.get_case('en', 'no-such-case').status_code, 404)

    def test_says_what_the_case_is_in_search_results_and_link_previews(self):
        for language, title, summary in [
            ('en', 'first-case title', 'first-case summary'),
            ('es', 'first-case título', 'first-case resumen'),
        ]:
            with self.subTest(language=language):
                response = self.get_case(language)
                url = f'http://testserver{reverse_in(language, "main:case-detail", slug="first-case")}'

                self.assertEqual(page_title(response), f'{title} - Nestor Bracho')
                self.assertEqual(meta(response, 'description'), summary)
                self.assertEqual(meta(response, 'og:title'), page_title(response))
                self.assertEqual(meta(response, 'og:description'), summary)
                self.assertEqual(meta(response, 'og:type'), 'article')
                self.assertEqual(meta(response, 'og:url'), url)
                self.assertContains(response, f'<link rel="canonical" href="{url}">')
                for other in ['en', 'es']:
                    other_url = reverse_in(other, 'main:case-detail', slug='first-case')
                    self.assertContains(
                        response, f'<link rel="alternate" hreflang="{other}" href="http://testserver{other_url}">'
                    )
                self.assertContains(
                    response,
                    '<link rel="alternate" hreflang="x-default" href="http://testserver/cases/first-case/">',
                )

    def test_is_a_work_by_the_person_the_site_is_about(self):
        data = structured_data(self.get_case('es'))

        self.assertEqual(data['@type'], 'CreativeWork')
        self.assertEqual(data['name'], 'first-case título')
        self.assertEqual(data['description'], 'first-case resumen')
        self.assertEqual(data['keywords'], 'Python, Django')
        self.assertEqual(data['inLanguage'], 'es')
        self.assertEqual(data['url'], f'http://testserver{reverse_in("es", "main:case-detail", slug="first-case")}')
        self.assertEqual(data['author']['@id'], 'http://testserver/#person')
        self.assertNotIn('image', data)

    def test_the_screenshot_is_the_works_image(self):
        data = structured_data(self.get_case('en', 'last-case'))

        self.assertEqual(data['image'], f'http://testserver{static("images/og-default.png")}')

    def test_the_sitemap_lists_published_cases_only(self):
        response = self.client.get(reverse('sitemap'))

        for language in ['en', 'es']:
            published = reverse_in(language, 'main:case-detail', slug='first-case')
            self.assertContains(response, f'<loc>http://testserver{published}</loc>')
        self.assertNotContains(response, 'drafted-case')


@override_settings(DEBUG=True)
@mock.patch(
    'main.cases.CASES',
    [make_case('published-case'), make_case('drafted-case', published=False, problem=None, result=None)],
)
class CaseDraftsInDevelopmentTests(TestCase):
    """In development the drafts are shown, marked, so Nestor can review them on the real page."""

    def test_drafts_are_shown_and_marked(self):
        response = self.client.get(reverse_in('en', 'main:case-detail', slug='drafted-case'))

        self.assertContains(response, 'drafted-case title')
        self.assertContains(response, '<p class="dev-mark">Development only: not published</p>')
        # What it lacks is left out, not marked
        self.assertEqual(
            case_labels(response), ['01 / What I built', '02 / How it was built', '03 / Stack', '04 / Links']
        )

    def test_the_home_marks_them_too(self):
        response = self.client.get(reverse_in('en', 'main:index'))

        self.assertEqual(card_titles(response), ['published-case title', 'drafted-case title'])
        self.assertContains(response, 'class="dev-mark"', count=1)

    def test_the_sitemap_lists_them_too(self):
        response = self.client.get(reverse('sitemap'))

        self.assertContains(response, reverse_in('en', 'main:case-detail', slug='drafted-case'))

    def test_without_a_summary_the_site_description_stands_in(self):
        with mock.patch('main.cases.CASES', [make_case('no-summary', published=False, summary=None)]):
            response = self.client.get(reverse_in('en', 'main:case-detail', slug='no-summary'))

        self.assertIn(settings.OWNER_ROLE, meta(response, 'description'))
        self.assertNotIn('description', structured_data(response))

    def test_a_single_case_has_no_next_case(self):
        with mock.patch('main.cases.CASES', [make_case('only-case')]):
            response = self.client.get(reverse_in('en', 'main:case-detail', slug='only-case'))

        self.assertNotContains(response, 'next-case')
