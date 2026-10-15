import re
import time
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import NewsletterSubscriber


def last_message(response):
    # Redirects aren't followed, so earlier messages stay queued in front of the newest one
    return [str(message) for message in get_messages(response.wsgi_request)][-1]


class AddNewsletterSubscriberViewTests(TestCase):
    def setUp(self):
        # The site defaults to Spanish; the assertions read the English messages
        self.client.defaults['HTTP_ACCEPT_LANGUAGE'] = 'en'

    def subscribe(self, email, next_url='/about/'):
        return self.client.post(reverse('main:newsletter-subscriber'), {'email': email, 'next': next_url})

    def confirmation_link(self, email_message):
        return re.search(r'https?://\S+/newsletter/confirm/\S+/', email_message.body).group()

    def test_stores_a_pending_subscription_and_emails_the_link(self):
        response = self.subscribe('Reader@Example.com')

        self.assertRedirects(response, '/about/', fetch_redirect_response=False)
        subscriber = NewsletterSubscriber.objects.get(email='reader@example.com')
        self.assertIsNone(subscriber.confirmed_at)
        self.assertEqual(mail.outbox[0].to, ['reader@example.com'])
        # Tokens carry the time they were signed, so compare whose token it is rather than the text, which changes
        # when the test crosses into the next second
        token = self.confirmation_link(mail.outbox[0]).rstrip('/').rsplit('/', 1)[-1]
        self.assertEqual(NewsletterSubscriber.from_confirmation_token(token, max_age=60), subscriber)

    def test_the_emailed_link_confirms_the_subscription(self):
        self.subscribe('reader@example.com')

        response = self.client.get(self.confirmation_link(mail.outbox[0]))

        self.assertRedirects(response, reverse('main:index'), fetch_redirect_response=False)
        self.assertIsNotNone(NewsletterSubscriber.objects.get().confirmed_at)

    def test_expired_links_do_not_confirm(self):
        self.subscribe('reader@example.com')

        eight_days_later = time.time() + 8 * 24 * 60 * 60
        with mock.patch('django.core.signing.time.time', return_value=eight_days_later):
            response = self.client.get(self.confirmation_link(mail.outbox[0]))

        self.assertIn('invalid or has expired', last_message(response))
        self.assertIsNone(NewsletterSubscriber.objects.get().confirmed_at)

    def test_tampered_links_do_not_confirm(self):
        response = self.client.get(reverse('main:newsletter-confirm', args=['not-a-signed-token']))

        self.assertIn('invalid or has expired', last_message(response))

    def test_resends_the_link_to_pending_addresses(self):
        self.subscribe('reader@example.com')
        self.subscribe('reader@example.com')

        self.assertEqual(NewsletterSubscriber.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 2)

    def test_answers_the_same_for_confirmed_addresses_without_emailing_them(self):
        pending = self.subscribe('new@example.com')
        NewsletterSubscriber.objects.create(email='confirmed@example.com').confirm()
        mail.outbox.clear()

        confirmed = self.subscribe('confirmed@example.com')

        self.assertEqual(last_message(confirmed), last_message(pending))
        self.assertEqual(mail.outbox, [])

    def test_keeps_the_pending_subscription_when_the_email_fails(self):
        with (
            mock.patch('usermanager.views.send_mail', side_effect=OSError('SMTP is down')),
            self.assertLogs('usermanager.views', level='ERROR'),
        ):
            response = self.subscribe('reader@example.com')

        self.assertIn("couldn't send", last_message(response))
        self.assertTrue(NewsletterSubscriber.objects.filter(email='reader@example.com').exists())

    def test_ignores_bots_that_fill_the_hidden_field(self):
        self.client.post(
            reverse('main:newsletter-subscriber'), {'email': 'bot@example.com', 'contact_me_by_fax_only': 'spam'}
        )

        self.assertFalse(NewsletterSubscriber.objects.exists())
        self.assertEqual(mail.outbox, [])

    def test_never_redirects_to_another_site(self):
        response = self.subscribe('reader@example.com', next_url='https://evil.example/')

        self.assertRedirects(response, '/', fetch_redirect_response=False)


class NewsletterSubscriberAdminTests(TestCase):
    def test_list_loads(self):
        self.client.force_login(get_user_model().objects.create_superuser('admin'))
        NewsletterSubscriber.objects.create(email='reader@example.com')

        response = self.client.get(reverse('admin:usermanager_newslettersubscriber_changelist'))

        self.assertContains(response, 'reader@example.com')
