"""WSGI entry point, served by Gunicorn in production (deploy/gunicorn.service)."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
