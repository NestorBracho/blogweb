"""Runs the tests with the site's settings, less what only the server provides (TEST_RUNNER in config/settings.py).

nginx hands the site HTTPS requests, but the test client's are plain http, which SECURE_SSL_REDIRECT would send to
https. And collectstatic hasn't run: there is neither STATIC_ROOT, which WhiteNoise warns about, nor the list of hashed
file names that the production storage looks every static file up in.

Workers of `test --parallel` import this module before Django is set up, so it mustn't import any models.
"""

from django.conf import settings
from django.test import override_settings, runner


def settings_without_the_server():
    return override_settings(
        SECURE_SSL_REDIRECT=False,
        STATIC_ROOT=None,
        STORAGES={
            **settings.STORAGES,
            'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
        },
    )


def set_up_worker():
    """Runs in each worker of `test --parallel` that starts a new interpreter (spawn, the default on macOS) and so
    loads the settings anew. Returns the override, which lasts as long as the worker."""
    worker_settings = settings_without_the_server()
    worker_settings.enable()
    return worker_settings


class ParallelTestSuite(runner.ParallelTestSuite):
    process_setup = set_up_worker


class TestRunner(runner.DiscoverRunner):
    parallel_test_suite = ParallelTestSuite

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self.test_settings = settings_without_the_server()
        self.test_settings.enable()

    def teardown_test_environment(self, **kwargs):
        self.test_settings.disable()
        super().teardown_test_environment(**kwargs)
