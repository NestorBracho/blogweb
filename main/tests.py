import json
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.core import mail
from django.templatetags.static import static
from django.test import TestCase, override_settings
from django.urls import reverse, reverse_lazy

from .models import ContactRequest


class HomeTests(TestCase):
    def test_intro_is_translated(self):
        spanish = self.client.get(reverse('main:index'), headers={'Accept-Language': 'es'})
        english = self.client.get(reverse('main:index'), headers={'Accept-Language': 'en'})

        self.assertContains(spanish, 'Llevo más de 12 años construyendo plataformas web')
        self.assertContains(english, 'I have spent more than 12 years building web platforms')

    def test_says_who_i_am_in_search_results_and_link_previews(self):
        response = self.client.get(reverse('main:index'), headers={'Accept-Language': 'en'})

        self.assertContains(response, '<title>Nestor Bracho, Senior Backend Engineer</title>')
        self.assertContains(response, '<meta property="og:title" content="Nestor Bracho, Senior Backend Engineer">')
        self.assertContains(response, '<meta property="og:description" content="Senior backend engineer with more than')

    def test_points_from_the_role_to_the_personal_blog(self):
        spanish = self.client.get(reverse('main:index'), headers={'Accept-Language': 'es'})
        english = self.client.get(reverse('main:index'), headers={'Accept-Language': 'en'})

        self.assertContains(spanish, 'Fuera del trabajo, <a href="#blog">escribo aquí</a>')
        self.assertContains(english, 'Outside work, I <a href="#blog">write here</a>')
        self.assertContains(english, 'id="blog"')

    def test_footer_describes_the_site_in_each_language(self):
        spanish = self.client.get(reverse('main:index'), headers={'Accept-Language': 'es'})
        english = self.client.get(reverse('main:index'), headers={'Accept-Language': 'en'})

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
        spanish = self.client.get(reverse('main:index'), headers={'Accept-Language': 'es'})
        english = self.client.get(reverse('main:index'), headers={'Accept-Language': 'en'})

        self.assertContains(spanish, 'aria-label="Bracho, inicio"')
        self.assertContains(english, 'aria-label="Bracho, home"')


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


class PrivacyViewTests(TestCase):
    def test_shows_the_whole_policy_in_each_language(self):
        spanish = self.client.get(reverse('main:privacy'), headers={'Accept-Language': 'es'})
        english = self.client.get(reverse('main:privacy'), headers={'Accept-Language': 'en'})

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
        response = self.client.get(reverse('main:about'), HTTP_ACCEPT_LANGUAGE='en')

        self.assertContains(response, '<title>About Me - Nestor Bracho</title>')
        self.assertContains(response, '<meta property="og:image" content="http://testserver/static/')


@override_settings(OWNER_CV_PDF_URLS={'en': '/media/cv/cv-en.pdf', 'es': '/media/cv/cv-es.pdf'})
class CVViewTests(TestCase):
    url = reverse_lazy('main:cv')

    def test_shows_the_whole_cv_in_each_language(self):
        spanish = self.client.get(self.url, headers={'Accept-Language': 'es'})
        english = self.client.get(self.url, headers={'Accept-Language': 'en'})

        self.assertContains(spanish, 'Experiencia profesional')
        self.assertNotContains(spanish, 'Professional experience')
        self.assertContains(english, 'Professional experience')
        self.assertContains(english, '<title>CV - Nestor Bracho</title>')

    def test_offers_the_pdf_in_the_page_language(self):
        spanish = self.client.get(self.url, headers={'Accept-Language': 'es'})
        english = self.client.get(self.url, headers={'Accept-Language': 'en'})

        self.assertContains(spanish, 'href="/media/cv/cv-es.pdf"')
        self.assertContains(english, 'href="/media/cv/cv-en.pdf"')

    @override_settings(OWNER_CV_PDF_URLS={'en': '', 'es': ''})
    def test_hides_the_download_without_a_pdf(self):
        response = self.client.get(self.url, headers={'Accept-Language': 'en'})

        self.assertNotContains(response, 'Download PDF')

    @override_settings(OWNER_EMAIL='nestor@example.com', OWNER_LOCATION='Madrid, Spain')
    def test_gives_the_contact_details_when_configured(self):
        response = self.client.get(self.url)

        self.assertContains(response, 'href="mailto:nestor@example.com"')
        self.assertContains(response, 'Madrid, Spain')

    def test_is_linked_from_the_menu_and_the_sitemap(self):
        self.assertContains(self.client.get(reverse('main:index')), f'href="{self.url}"')
        self.assertContains(self.client.get(reverse('sitemap')), f'http://testserver{self.url}')

    def test_the_old_resume_post_redirects_here(self):
        response = self.client.get('/post/resume')

        self.assertRedirects(response, self.url, status_code=301)


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
        response = self.client.post(
            reverse('main:contact'), {**self.data, 'email': 'ada@'}, headers={'Accept-Language': 'en'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Ada"')
        self.assertContains(response, '>Hello!</textarea>')
        self.assertContains(response, 'aria-describedby="form-email-error"')
        self.assertContains(response, 'Enter a valid email address.')
        self.assertFalse(ContactRequest.objects.exists())
        self.assertEqual(mail.outbox, [])

    def test_is_marked_with_the_page_language(self):
        response = self.client.get(reverse('main:contact'), headers={'Accept-Language': 'es'})

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
