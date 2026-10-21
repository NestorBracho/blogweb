"""Logging filters used by LOGGING in config/settings.py."""

import logging
import time
import traceback


class OncePerError(logging.Filter):
    """Lets each error through once every `seconds` in each process, and drops the repeats.

    Error emails share the SMTP provider's daily quota (300 on Brevo's free plan) with the contact form and the
    newsletter: a page that fails for every visitor or crawler would use it up within hours. The console log still
    gets every occurrence; the email only has to say that something broke.
    """

    def __init__(self, seconds):
        super().__init__()
        self.seconds = seconds
        self.last_passed = {}

    def filter(self, record):
        error, now = error_source(record), time.monotonic()
        if error in self.last_passed and now - self.last_passed[error] < self.seconds:
            return False
        self.last_passed[error] = now
        return True


def error_source(record):
    """The exception and the line that raised it; without an exception, the logger and message."""
    if record.exc_info and record.exc_info[2]:
        frame = traceback.extract_tb(record.exc_info[2])[-1]
        return record.exc_info[0], frame.filename, frame.lineno
    return record.name, record.msg
