from django.test import TestCase, override_settings
from django.urls import reverse


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
