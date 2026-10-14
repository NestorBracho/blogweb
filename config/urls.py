"""Root URLs: the admin, i18n, sitemap, robots.txt and favicon, plus the pages from main and blog."""

from django.conf import settings
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
    path('i18n/setlang/', set_language, name='set_language'),
    path(settings.ADMIN_URL, admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots'),
    # Browsers and crawlers ask for /favicon.ico at the root. The hashed file name is looked up per request (lazy):
    # deploys run migrate, which imports this module, before collectstatic. A temporary redirect, so browsers don't
    # remember one hashed name forever.
    path('favicon.ico', RedirectView.as_view(url=lazy(static_url, str)('favicon/favicon.ico')), name='favicon'),
    # The CV used to be a blog post; keep old links working
    path('post/resume', RedirectView.as_view(pattern_name='main:cv', permanent=True)),
    path('', include('main.urls')),
    path('', include('blog.urls')),
]

# In production nginx serves media files; static() is a no-op when DEBUG is False
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
