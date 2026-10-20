"""Root URLs.

Pages carry their language in the path (/en/…, /es/…); a path without one is redirected to the visitor's language
by LocaleMiddleware (docs/adr/0006-language-in-the-url.md). The admin, the API, the sitemap, robots.txt and the
favicon stay at the root.
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.templatetags.static import static as static_url
from django.urls import include, path
from django.utils.functional import lazy
from django.views.generic import RedirectView, TemplateView
from django.views.i18n import set_language

from blog.sitemaps import CategorySitemap, PostSitemap
from main.sitemaps import StaticViewSitemap

sitemaps = {
    'pages': StaticViewSitemap,
    'posts': PostSitemap,
    'categories': CategorySitemap,
}

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # The page sends X-Language, so the API needs no prefix (and writes aren't redirected)
    path('api/', include('blog.api.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots'),
    # Browsers and crawlers ask for /favicon.ico at the root. The hashed file name is looked up per request (lazy):
    # deploys run migrate, which imports this module, before collectstatic. A temporary redirect, so browsers don't
    # remember one hashed name forever.
    path('favicon.ico', RedirectView.as_view(url=lazy(static_url, str)('favicon/favicon.ico')), name='favicon'),
]

urlpatterns += i18n_patterns(
    # Under the prefix, the language switcher resolves the page it was sent from in that page's language
    path('i18n/setlang/', set_language, name='set_language'),
    # The CV used to be a blog post; keep old links working. Before blog.urls, which would take "resume" as a slug.
    path('post/resume', RedirectView.as_view(pattern_name='main:cv', permanent=True)),
    path('', include('main.urls')),
    path('', include('blog.urls')),
)

# In production nginx serves media files; static() is a no-op when DEBUG is False
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
