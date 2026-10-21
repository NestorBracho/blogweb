"""Tests for site-wide settings: error emails (LOGGING in config/settings.py) and the email_admins command, HTTPS, and
the test runner."""

import logging
import smtplib
from io import StringIO
from unittest import mock

from django.conf import settings
from django.core import mail
from django.core.management import CommandError, call_command
from django.templatetags.static import static
from django.test import SimpleTestCase, TestCase, override_settings

from config.log import OncePerError
from config.test_runner import TestRunner
from config.testing import reverse_in

ADMINS = [('ops@example.com', 'ops@example.com')]


def fail(*args, **kwargs):
    raise RuntimeError('Something broke')


def fail_elsewhere(*args, **kwargs):
    raise RuntimeError('Something else broke')


# The test runner sets DEBUG to False, as in production
@override_settings(ADMINS=ADMINS)
class ErrorEmailTests(TestCase):
    def setUp(self):
        self.client.raise_request_exception = False
        for handler in logging.getLogger('django').handlers:
            # The filter remembers the errors it let through: each test starts with none
            for log_filter in handler.filters:
                if isinstance(log_filter, OncePerError):
                    log_filter.last_passed.clear()
            # Keep the tracebacks these tests expect out of the test output
            if type(handler) is logging.StreamHandler:
                self.enterContext(mock.patch.object(handler, 'stream', StringIO()))

    def get_failing_page(self, failure=fail):
        with mock.patch('main.views.AboutView.get_context_data', failure):
            return self.client.get(reverse_in('en', 'main:about'))

    def test_a_server_error_emails_the_admins(self):
        response = self.get_failing_page()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['ops@example.com'])
        self.assertTrue(email.subject.startswith('[nestorbracho.com] ERROR'))
        self.assertIn('/en/about/', email.subject)
        self.assertIn('RuntimeError at /en/about/\nSomething broke', email.body)

    def test_the_same_error_is_emailed_once(self):
        for _ in range(3):
            self.assertEqual(self.get_failing_page().status_code, 500)
        self.get_failing_page(fail_elsewhere)

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('Something broke', mail.outbox[0].body)
        self.assertIn('Something else broke', mail.outbox[1].body)

    @override_settings(ADMINS=[])
    def test_nobody_is_emailed_without_admins(self):
        self.assertEqual(self.get_failing_page().status_code, 500)
        self.assertEqual(mail.outbox, [])

    def test_missing_pages_and_unknown_hosts_email_nobody(self):
        missing_page = self.client.get('/en/no-such-page/')
        unknown_host = self.client.get(reverse_in('en', 'main:about'), headers={'host': 'bot.example'})

        self.assertEqual(missing_page.status_code, 404)
        self.assertEqual(unknown_host.status_code, 400)
        self.assertEqual(mail.outbox, [])


class OncePerErrorTests(TestCase):
    def test_lets_an_error_through_again_once_the_time_is_up(self):
        log_filter = OncePerError(seconds=60)
        record = logging.makeLogRecord({'name': 'django.request', 'msg': 'Internal Server Error: %s'})

        with mock.patch('config.log.time.monotonic', side_effect=[1000, 1059, 1060]):
            self.assertEqual([log_filter.filter(record) for _ in range(3)], [True, False, True])


@override_settings(ADMINS=ADMINS)
class EmailAdminsCommandTests(TestCase):
    def test_emails_the_admins(self):
        output = StringIO()

        call_command('email_admins', 'Backup failed', 'rclone copy exited with 1', stdout=output)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['ops@example.com'])
        self.assertEqual(mail.outbox[0].subject, '[nestorbracho.com] Backup failed')
        self.assertEqual(mail.outbox[0].body, 'rclone copy exited with 1')
        self.assertIn('Emailed ops@example.com', output.getvalue())

    @override_settings(ADMINS=[])
    def test_fails_without_admins(self):
        with self.assertRaisesMessage(CommandError, 'ADMINS is empty'):
            call_command('email_admins', 'Backup failed', 'Details')

    def test_fails_when_the_email_cannot_be_sent(self):
        with mock.patch('main.management.commands.email_admins.mail_admins', side_effect=smtplib.SMTPException('down')):
            with self.assertRaisesMessage(CommandError, 'Could not send the email: down'):
                call_command('email_admins', 'Backup failed', 'Details')


# The test runner turns the redirect off for the other tests (config/test_runner.py)
@override_settings(SECURE_SSL_REDIRECT=True)
class HTTPSTests(TestCase):
    """nginx hands the site every request over plain http, and says in X-Forwarded-Proto how the visitor sent it."""

    def test_plain_http_is_redirected_to_https(self):
        url = reverse_in('en', 'main:about')

        response = self.client.get(url)

        self.assertRedirects(response, f'https://testserver{url}', status_code=301, fetch_redirect_response=False)

    def test_requests_that_came_over_https_are_not_redirected_again(self):
        response = self.client.get(reverse_in('en', 'main:about'), headers={'X-Forwarded-Proto': 'https'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.is_secure())


class TestRunnerTests(SimpleTestCase):
    def test_tests_need_neither_https_nor_collectstatic(self):
        self.assertFalse(settings.SECURE_SSL_REDIRECT)
        self.assertEqual(static('favicon/favicon.ico'), '/static/favicon/favicon.ico')

    def test_parallel_workers_that_load_the_settings_anew_get_the_same(self):
        # What a worker started with spawn has before its setup: the settings as the environment gives them
        with override_settings(SECURE_SSL_REDIRECT=True, STATIC_ROOT='/srv/blog/staticfiles'):
            worker_settings = TestRunner.parallel_test_suite.process_setup()
            try:
                self.assertFalse(settings.SECURE_SSL_REDIRECT)
                self.assertIsNone(settings.STATIC_ROOT)
            finally:
                worker_settings.disable()
