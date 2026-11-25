"""
Schema.org data (JSON-LD) that tells search engines who the site is about and what each post is. Views put it in the
`structured_data` context variable, one object or a list of them with the page's main entity first, and the page's
<head> renders each as its own block. The blog's and the main app's views both use it, so it lives here rather than
in either app.
"""

from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

from config.context_processors import site_description
from main.cases import E3_PYPI_URL, SITE_REPO_URL

NAME = 'Nestor Bracho'


def person(request):
    """The person the site is about, in the page's language."""
    # Only public details: email, phone and street stay in .env, off the public repo and the markup. Of where he
    # lives, only the city and the country.
    profiles = [settings.OWNER_LINKEDIN_URL, settings.OWNER_GITHUB_URL, E3_PYPI_URL, SITE_REPO_URL]
    return {
        '@type': 'Person',
        # The same person in both languages
        '@id': request.build_absolute_uri('/#person'),
        'name': NAME,
        'url': request.build_absolute_uri(reverse('main:index')),
        'jobTitle': settings.OWNER_ROLE,
        'image': request.build_absolute_uri(static('images/01-1.webp')),
        # In the past: that work ended and he is freelance now
        'alumniOf': {'@type': 'Organization', 'name': _('World Bank Group'), 'url': 'https://www.worldbank.org/'},
        'address': {
            '@type': 'PostalAddress',
            'addressLocality': settings.OWNER_CITY,
            'addressCountry': settings.OWNER_COUNTRY,
        },
        'knowsLanguage': ['es', 'en'],
        'sameAs': [url for url in profiles if url],
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


def website(request):
    """The site itself, published by the person it is about, in the page's language."""
    return {
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        '@id': request.build_absolute_uri('/#website'),
        'name': NAME,
        'url': request.build_absolute_uri(reverse('main:index')),
        'inLanguage': translation.get_language(),
        'publisher': {'@id': person(request)['@id']},
    }


def breadcrumbs(request, trail):
    """Where a page sits in the site: `trail` is [(name, URL)...], from the home to the page itself."""
    return {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': position, 'name': name, 'item': request.build_absolute_uri(url)}
            for position, (name, url) in enumerate(trail, start=1)
        ],
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
    url = request.build_absolute_uri(case.url)
    data = {
        '@context': 'https://schema.org',
        '@type': 'CreativeWork',
        'name': case.title,
        'url': url,
        'mainEntityOfPage': url,
        'inLanguage': translation.get_language(),
        # The whole Person, not only a reference: a page is often all a crawler reads of the site
        'author': person(request),
    }
    # Only what is written: unpublished cases, with fields still missing, exist in development alone
    if case.summary:
        data['description'] = case.summary
    if case.stack:
        data['keywords'] = ', '.join(case.stack)
    if case.screenshot:
        data['image'] = request.build_absolute_uri(static(case.screenshot['path']))
    return data


def case_page(request, case):
    """A case's page: the case study, then where it sits (the home's cases section: there is no cases page)."""
    home = reverse('main:index')
    trail = [(_('Home'), home), (_('Cases'), f'{home}#cases'), (case.title, case.url)]
    return [case_study(request, case), breadcrumbs(request, trail)]


def service_page(request, service):
    """A service's page (main/services.py, localized): where it sits, under the home. There is no services page."""
    return breadcrumbs(request, [(_('Home'), reverse('main:index')), (service.name, service.url)])


def how_i_work_page(request):
    return breadcrumbs(request, [(_('Home'), reverse('main:index')), (_('How I work'), reverse('main:how-i-work'))])


def blog_posting(request, post):
    data = {
        '@context': 'https://schema.org',
        '@type': 'BlogPosting',
        'headline': post.title(),
        'description': post.description(),
        'url': request.build_absolute_uri(post.get_absolute_url()),
        'mainEntityOfPage': request.build_absolute_uri(post.get_absolute_url()),
        'inLanguage': translation.get_language(),
        'datePublished': post.published_at.isoformat(),
        # When its content last changed, not when it was last saved (Post.content_modified)
        'dateModified': post.content_modified.isoformat(),
        'author': person(request),
    }
    if post.cover:
        data['image'] = request.build_absolute_uri(post.cover_urls['social'])
    return data


def post_page(request, post):
    """A post's page: the post, then where it sits (home, blog, post)."""
    trail = [
        (_('Home'), reverse('main:index')),
        (_('Blog'), reverse('blog:post-list')),
        (post.title(), post.get_absolute_url()),
    ]
    return [blog_posting(request, post), breadcrumbs(request, trail)]


def home(request):
    """The home's: the person, then the site."""
    return [home_page(request), website(request)]
