"""
URL configuration for personal_web_2 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from django.views.i18n import set_language
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

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
    path('', include('main.urls')),
    path('', include('blog.urls')),
]

# In production nginx serves media files; static() is a no-op when DEBUG is False
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
