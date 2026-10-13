from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ContactRequest


class RobotsTxtTests(TestCase):
    def test_points_crawlers_to_the_sitemap(self):
        response = self.client.get(reverse('robots'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertContains(response, f'Sitemap: http://testserver{reverse("sitemap")}')


class AboutViewTests(TestCase):
    def test_uses_its_own_meta_tags(self):
        response = self.client.get(reverse('main:about'), HTTP_ACCEPT_LANGUAGE='en')

        self.assertContains(response, '<title>About Me - Bracho</title>')
        self.assertContains(response, '<meta property="og:image" content="http://testserver/static/')


@override_settings(OWNER_GITHUB_URL='https://github.com/example', OWNER_LINKEDIN_URL='')
class SocialLinksTests(TestCase):
    def test_links_configured_profiles_only(self):
        response = self.client.get(reverse('main:index'))

        # Footer and sidebar both render the list
        self.assertContains(response, 'href="https://github.com/example"', count=2)
        self.assertNotContains(response, 'fa-linkedin"')

    @override_settings(OWNER_LINKEDIN_URL='https://www.linkedin.com/in/example')
    def test_links_linkedin_when_configured(self):
        response = self.client.get(reverse('main:index'))

        self.assertContains(response, 'href="https://www.linkedin.com/in/example"', count=2)


class ContactFormViewTests(TestCase):
    data = {'name': 'Ada', 'email': 'ada@example.com', 'message': 'Hello!'}

    def test_stores_the_request_and_emails_it(self):
        response = self.client.post(reverse('main:contact'), self.data)

        self.assertRedirects(response, reverse('main:index'), fetch_redirect_response=False)
        self.assertTrue(ContactRequest.objects.filter(email='ada@example.com').exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].reply_to, ['ada@example.com'])

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
