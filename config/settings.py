"""
Settings for nestorbracho.com. Anything that differs between a laptop and the server comes from the environment
(the .env file); .env.example lists the production values.
"""

import os
from pathlib import Path

import environ

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    ADMINS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
    ADMIN_URL=(str, 'admin/'),
    EMAIL_PORT=(int, 587),
    EMAIL_USE_TLS=(bool, True),
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')

# Debugging only: error pages with tracebacks, and runserver serving static and media files. Never on the server.
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env('ALLOWED_HOSTS')
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS')

# Admin lives under a non-default path in production to cut down on bot traffic
ADMIN_URL = env('ADMIN_URL')


# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
]
LOCAL_APPS = [
    'blog.apps.BlogConfig',
    'main.apps.MainConfig',
    'usermanager.apps.UsermanagerConfig',
]

EXTERNAL_APPS = [
    'rest_framework',
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + EXTERNAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'config.middleware.ContentSecurityPolicyMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.context_processors.sidebar',
                'config.context_processors.owner',
                'config.context_processors.newsletter',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': env('SQLITE_PATH', default=str(BASE_DIR / 'db.sqlite3')),
        'OPTIONS': {
            # WAL + busy timeout keep SQLite happy with several gunicorn workers
            'init_command': 'PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;',
            'timeout': 20,
            'transaction_mode': 'IMMEDIATE',
        },
    }
}

REST_FRAMEWORK = {
    # Staff sign in through the admin and the API takes that session. Not Basic auth, which would let anyone try
    # passwords against the API without knowing the admin's path.
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'blog.api.pagination.PageSizePagination',
    'DEFAULT_PERMISSION_CLASSES': [
        'blog.api.permissions.IsAdminOrReadOnly',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    # Counted per Gunicorn worker (config/throttling.py)
    'DEFAULT_THROTTLE_CLASSES': [
        'config.throttling.AnonRateThrottle',
        'config.throttling.UserRateThrottle',
        'config.throttling.WriteRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/minute',
        'user': '120/minute',
        'write': '60/hour',
        # Contact and newsletter forms (config/throttling.FormThrottle), which send emails
        'contact': '5/hour',
        'newsletter': '5/hour',
    },
}

# Email config

EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='webmaster@localhost')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_SUBJECT_PREFIX = '[nestorbracho.com] '

# Who gets an email when a page fails with a server error (LOGGING below) or a nightly backup fails
# (deploy/backup.sh). Comma-separated addresses in the environment; empty, nobody does.
ADMINS = [(address, address) for address in map(str.strip, env('ADMINS'))]

# Address that receives contact form submissions
CONTACT_EMAIL = env('CONTACT_EMAIL', default=DEFAULT_FROM_EMAIL)


# Personal details shown on the site (resume, about...). Kept out of the repo on purpose.

OWNER_EMAIL = env('OWNER_EMAIL', default='')
OWNER_PHONE = env('OWNER_PHONE', default='')
# Where he lives, in English; OWNER_LOCATION_ES is the Spanish version, the English one when unset
OWNER_LOCATIONS = {
    'en': env('OWNER_LOCATION', default=''),
}
OWNER_LOCATIONS['es'] = env('OWNER_LOCATION_ES', default=OWNER_LOCATIONS['en'])

# Job title on the home page, the CV, page titles and link previews. It changes now and then, so it lives here only.
OWNER_ROLE = 'Senior Full Stack Engineer'

# The year his career started (January), for the "more than N years" on the home page, the CV and link previews
OWNER_CAREER_START_YEAR = 2013

# The CV as a PDF in each language, linked from /cv/. They hold the phone number, so they live on the server
# (e.g. under MEDIA_ROOT/cv/), not in the repo. Leave one empty to hide its download button.
OWNER_CV_PDF_URLS = {
    'en': env('OWNER_CV_PDF_EN', default=''),
    'es': env('OWNER_CV_PDF_ES', default=''),
}

# Public profiles linked from the footer and sidebar. Leave one empty to hide its icon.
OWNER_GITHUB_URL = env('OWNER_GITHUB_URL', default='https://github.com/NestorBracho')
OWNER_LINKEDIN_URL = env('OWNER_LINKEDIN_URL', default='https://www.linkedin.com/in/nestor-bracho')


# The newsletter sign-up in the sidebar and its part of the privacy policy. Off until something sends the newsletter
# (and its unsubscribe link); the sign-up views and their double opt-in keep working either way.
NEWSLETTER_ENABLED = env.bool('NEWSLETTER_ENABLED', default=False)


# OpenAI, only needed by the draft_article command

OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
# The model that writes the article and the one that draws its cover
OPENAI_MODEL = env('OPENAI_MODEL', default='gpt-6-astra')
OPENAI_IMAGE_MODEL = env('OPENAI_IMAGE_MODEL', default='gpt-image-2.5-flare')


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

# Pages live under /en/ and /es/ (i18n_patterns in config/urls.py). English is what crawlers, link previews and
# visitors who ask for neither language get; docs/adr/0006-language-in-the-url.md
LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static & media files
# https://docs.djangoproject.com/en/5.2/howto/static-files/
# Static files are served by WhiteNoise; media files by nginx straight from MEDIA_ROOT.

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = env('STATIC_ROOT', default=str(BASE_DIR / 'staticfiles'))

MEDIA_URL = '/media/'
MEDIA_ROOT = env('MEDIA_ROOT', default=str(BASE_DIR / 'media'))

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    # Compressed copies, with a hash of their contents in the name so browsers can cache them for good. collectstatic
    # writes the list of names; with DEBUG on, pages link the files by their plain names and don't need it.
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# WhiteNoise doesn't know this extension and would serve the web app manifest as application/octet-stream
WHITENOISE_MIMETYPES = {'.webmanifest': 'application/manifest+json'}

# Uploaded covers can be large; keep them on disk instead of in memory
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024


# Content-Security-Policy: where pages may load scripts, styles, fonts and images from. Scripts only come from the
# site itself (no inline ones), so injected HTML can't run code. Same setting as Django 6's built-in CSP support.
SECURE_CSP = {
    'default-src': ["'self'"],
    'script-src': ["'self'"],
    # The theme uses style="" attributes
    'style-src': ["'self'", "'unsafe-inline'"],
    # Posts can show images hosted on other sites
    'img-src': ["'self'", 'https:'],
    'object-src': ["'none'"],
    'base-uri': ["'self'"],
    'form-action': ["'self'"],
    'frame-ancestors': ["'none'"],
}


# HTTPS and security headers
# The site is only served over HTTPS: nginx and Cloudflare terminate TLS and forward the original scheme. To serve it
# over plain http, as runserver does, turn the redirect and the secure cookies off in the environment (README.md).

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)
# Only sent over HTTPS, so a laptop never gets it
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=60 * 60 * 24 * 30)
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'

SILENCED_SYSTEM_CHECKS = [
    # HSTS covers this domain alone, on purpose: not its subdomains (W005), and not the preload list built into
    # browsers (W021), which takes months to leave
    'security.W005',
    'security.W021',
]


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'},
        'once_per_error': {'()': 'config.log.OncePerError', 'seconds': 60 * 60},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
        # Emails ADMINS the errors Django logs, such as a page that fails with a 500, with the traceback. Only in
        # production, and each error once an hour at most.
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false', 'once_per_error'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        # A request for a host the site doesn't serve comes from a bot, not from a bug: log it without an email
        'django.security.DisallowedHost': {
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

# Tests run without what only the server provides: HTTPS from nginx, and collectstatic's files
TEST_RUNNER = 'config.test_runner.TestRunner'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
