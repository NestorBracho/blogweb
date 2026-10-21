from django.conf import settings
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Email ADMINS a subject and a message through the site's SMTP server. deploy/backup.sh uses it to report a "
        'backup that failed.'
    )

    def add_arguments(self, parser):
        parser.add_argument('subject')
        parser.add_argument('message')

    def handle(self, *args, subject, message, **options):
        if not settings.ADMINS:
            raise CommandError('ADMINS is empty, so there is nobody to email: set it in .env')
        try:
            mail_admins(subject, message)
        except OSError as error:  # SMTP errors included
            raise CommandError(f'Could not send the email: {error}') from error
        self.stdout.write(f'Emailed {", ".join(address for _, address in settings.ADMINS)}')
