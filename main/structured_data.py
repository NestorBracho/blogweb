"""
Schema.org data (JSON-LD) that tells search engines who the site is about and what each post is. Views put it in the
`structured_data` context variable and the page's <head> renders it.
"""

from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils import translation

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


def home_page(request):
    return {'@context': 'https://schema.org', **person(request)}


def profile_page(request):
    return {
        '@context': 'https://schema.org',
        '@type': 'ProfilePage',
        'url': request.build_absolute_uri(request.path),
        'inLanguage': translation.get_language(),
        'mainEntity': person(request),
    }


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
        # Posts have no publication date of their own: the page and the feed show when they were created
        'datePublished': post.created.isoformat(),
        'dateModified': post.updated.isoformat(),
        'author': {'@type': 'Person', '@id': author['@id'], 'name': author['name'], 'url': author['url']},
    }
    if post.cover:
        data['image'] = request.build_absolute_uri(post.cover_urls['social'])
    return data
