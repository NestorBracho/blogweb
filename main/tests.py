from django.test import TestCase
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
