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
from config.testing import reverse_in, structured_data

from . import seo
from .models import ContactRequest


class HomeTests(TestCase):
    def test_intro_is_translated(self):
        spanish = self.client.get(reverse_in('es', 'main:index'))
        english = self.client.get(reverse_in('en', 'main:index'))

        self.assertContains(spanish, 'Llevo más de 12 años construyendo plataformas web')
        self.assertContains(english, 'I have spent more than 12 years building web platforms')

    def test_says_who_i_am_in_search_results_and_link_previews(self):
        response = self.client.get(reverse_in('en', 'main:index'))

        self.assertContains(response, '<title>Nestor Bracho, Senior Full Stack Engineer</title>')
        self.assertContains(response, '<meta property="og:title" content="Nestor Bracho, Senior Full Stack Engineer">')
        self.assertContains(response, '<meta property="og:description" content="Senior Full Stack Engineer with more')

    @override_settings(OWNER_ROLE='Staff Engineer')
    def test_the_role_is_set_in_one_place(self):
        home = self.client.get(reverse_in('es', 'main:index'))
        cv = self.client.get(reverse_in('es', 'main:cv'))

        self.assertContains(home, '<title>Nestor Bracho, Staff Engineer</title>')
        self.assertContains(home, '<meta name="description" content="Staff Engineer con más de 12 años')
        self.assertContains(home, '<p class="hero__subtitle">Staff Engineer · Python/Django</p>')
        self.assertContains(cv, '<p class="cv__headline">Staff Engineer · Python/Django</p>')
        self.assertContains(cv, '<meta name="description" content="CV de Nestor Bracho, Staff Engineer con más')
        # The CV's job history keeps its own titles; only the headline follows the setting
        self.assertNotContains(cv, '<p class="cv__headline">Senior Full Stack Engineer')

    def test_points_from_the_role_to_the_personal_blog(self):
        spanish = self.client.get(reverse_in('es', 'main:index'))
        english = self.client.get(reverse_in('en', 'main:index'))

        self.assertContains(spanish, 'Fuera del trabajo, <a href="#blog">escribo aquí</a>')
        self.assertContains(english, 'Outside work, I <a href="#blog">write here</a>')
        self.assertContains(english, 'id="blog"')

    def test_footer_describes_the_site_in_each_language(self):
        spanish = self.client.get(reverse_in('es', 'main:index'))
        english = self.client.get(reverse_in('en', 'main:index'))

        self.assertContains(spanish, 'Ciencia, historias y software. Esta es la web personal de Nestor Bracho')
        self.assertContains(english, 'Science, storytelling &amp; software. This is the personal site of Nestor Bracho')

    def test_leads_to_the_cv_and_the_contact_form(self):
        response = self.client.get(reverse('main:index'))

        self.assertContains(response, f'href="{reverse("main:cv")}" class="button button--primary"')
        self.assertContains(response, f'href="{reverse("main:contact")}" class="button button--secondary"')


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
    def test_every_font_the_stylesheets_declare_is_a_file_of_the_site(self):
        for stylesheet in ['css/main.css']:
            for url in re.findall(r'url\(([^)]+)\)', Path(finders.find(stylesheet)).read_text()):
                with self.subTest(stylesheet=stylesheet, url=url):
                    self.assertIsNotNone(finders.find(posixpath.normpath(posixpath.join('css', url))))

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
                response = self.client.get(url)

                self.assertContains(response, '<title>Page not found - Nestor Bracho</title>', status_code=404)
                self.assertContains(response, 'Back to homepage', status_code=404)
                self.assertNotContains(response, 'rel="canonical"', status_code=404)
                self.assertNotContains(response, 'hreflang', status_code=404)
                self.assertNotContains(response, 'og:url', status_code=404)

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


class ContactFormViewTests(TestCase):
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


class ContactRequestAdminTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser('admin'))
        self.request = ContactRequest.objects.create(name='Ada', email='ada@example.com', message='Hello!')

    def test_requests_can_be_read_but_not_created(self):
        expected_status = {
            reverse('admin:main_contactrequest_changelist'): 200,
            reverse('admin:main_contactrequest_change', args=[self.request.pk]): 200,
            reverse('admin:main_contactrequest_add'): 403,
        }
        for url, status in expected_status.items():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status)
