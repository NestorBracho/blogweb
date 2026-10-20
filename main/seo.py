"""The addresses search engines and link previews need for a page: its canonical URL and its other languages."""

from django.conf import settings
from django.urls import reverse
from django.utils import translation
from django.utils.http import urlencode

# Query parameters that change what a page shows. Anything else (utm_source, fbclid...) only says how a visitor
# arrived, so it stays out of the canonical URL.
PAGE_PARAMETERS = ['page']

# og:locale wants a territory too
OPEN_GRAPH_LOCALES = {'en': 'en_US', 'es': 'es_ES'}


def page_urls(request):
    """
    The page's canonical URL, the same page in each language and the x-default address (without a language, so it
    redirects visitors to theirs), all absolute. None for anything that isn't a page in one language: no request
    (Django renders the 500 page without one), no URL pattern behind it, or an address outside the language prefixes.
    """
    match = getattr(request, 'resolver_match', None)
    if match is None or translation.get_language_from_path(request.path_info) is None:
        return None

    query = urlencode([(name, request.GET[name]) for name in PAGE_PARAMETERS if name in request.GET])

    def absolute(path):
        return request.build_absolute_uri(f'{path}?{query}' if query else path)

    paths = {}
    for language, _name in settings.LANGUAGES:
        with translation.override(language):
            paths[language] = reverse(match.view_name, args=match.args, kwargs=match.kwargs)
    # Same rule as the sitemap's x-default (django.contrib.sitemaps)
    default = paths[settings.LANGUAGE_CODE].replace(f'/{settings.LANGUAGE_CODE}/', '/', 1)

    return {
        'canonical': absolute(request.path),
        'languages': [(language, absolute(path)) for language, path in paths.items()],
        'x_default': absolute(default),
    }


def open_graph_locale(language):
    return OPEN_GRAPH_LOCALES.get(language, language)
