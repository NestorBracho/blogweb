from django.test import TestCase
from django.urls import reverse

from .models import NewsletterSubscriber


class AddNewsletterSubscriberViewTests(TestCase):
    def subscribe(self, email, next_url='/about/'):
        return self.client.post(reverse('main:newsletter-subscriber'), {'email': email, 'next': next_url})

    def test_subscribes_and_returns_to_the_page(self):
        response = self.subscribe('reader@example.com')

        self.assertRedirects(response, '/about/', fetch_redirect_response=False)
        self.assertTrue(NewsletterSubscriber.objects.filter(email='reader@example.com').exists())

    def test_never_redirects_to_another_site(self):
        response = self.subscribe('reader@example.com', next_url='https://evil.example/')

        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_rejects_an_email_that_is_already_subscribed(self):
        NewsletterSubscriber.objects.create(email='reader@example.com')

        response = self.subscribe('reader@example.com')

        self.assertRedirects(response, '/about/', fetch_redirect_response=False)
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)
