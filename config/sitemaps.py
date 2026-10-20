from django.contrib.sitemaps import Sitemap


class TranslatedSitemap(Sitemap):
    """Lists every page once per language, each with links to its other versions.

    The x-default link is the page without a language prefix, which redirects visitors to their language.
    """

    i18n = True
    alternates = True
    x_default = True
