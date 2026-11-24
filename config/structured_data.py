"""
Schema.org data (JSON-LD) that tells search engines who the site is about and what each post is. Views put it in the
`structured_data` context variable and the page's <head> renders it. The blog's and the main app's views both use it,
so it lives here rather than in either app.
"""

from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils import translation

from config.context_processors import site_description

NAME = 'Nestor Bracho'


def person(request):
    # Only public details: email, phone and location live in .env so they stay off the public repo and the markup
    return {
        '@type': 'Person',
        # The same person in both languages
        '@id': request.build_absolute_uri('/#person'),
        'name': NAME,
        'url': request.build_absolute_uri(reverse('main:index')),
        'jobTitle': settings.OWNER_ROLE,
        'image': request.build_absolute_uri(static('images/01-1.webp')),
        'sameAs': [url for url in [settings.OWNER_LINKEDIN_URL, settings.OWNER_GITHUB_URL] if url],
    }


# The home's profile card's stack (main/_lib/_profile_card.html), with the names written out ("DRF" there). The card
# has its own copy: change both together.
KNOWS_ABOUT = ['Python', 'Django', 'Django REST Framework', 'PostgreSQL', 'AWS']


def home_page(request):
    """The home is about the person: what he does, in the page's language, and what he works with."""
    return {
        '@context': 'https://schema.org',
        **person(request),
        # The same text as the home's meta and Open Graph descriptions
        'description': site_description(),
        'knowsAbout': KNOWS_ABOUT,
    }


def profile_page(request):
    return {
        '@context': 'https://schema.org',
        '@type': 'ProfilePage',
        'url': request.build_absolute_uri(request.path),
        'inLanguage': translation.get_language(),
        'mainEntity': person(request),
    }


def case_study(request, case):
    """A case study (main/cases.py, localized) in the page's language, by the person the site is about."""
    author = person(request)
    url = request.build_absolute_uri(case.url)
    data = {
        '@context': 'https://schema.org',
        '@type': 'CreativeWork',
        'name': case.title,
        'url': url,
        'mainEntityOfPage': url,
        'inLanguage': translation.get_language(),
        'author': {'@type': 'Person', '@id': author['@id'], 'name': author['name'], 'url': author['url']},
    }
    # Only what is written: unpublished cases, with fields still missing, exist in development alone
    if case.summary:
        data['description'] = case.summary
    if case.stack:
        data['keywords'] = ', '.join(case.stack)
    if case.screenshot:
        data['image'] = request.build_absolute_uri(static(case.screenshot['path']))
    return data


def blog_posting(request, post):
    author = person(request)
    data = {
        '@context': 'https://schema.org',
        '@type': 'BlogPosting',
        'headline': post.title(),
        'description': post.description(),
        'url': request.build_absolute_uri(post.get_absolute_url()),
        'mainEntityOfPage': request.build_absolute_uri(post.get_absolute_url()),
        'inLanguage': translation.get_language(),
        'datePublished': post.published_at.isoformat(),
        'dateModified': post.updated.isoformat(),
        'author': {'@type': 'Person', '@id': author['@id'], 'name': author['name'], 'url': author['url']},
    }
    if post.cover:
        data['image'] = request.build_absolute_uri(post.cover_urls['social'])
    return data
