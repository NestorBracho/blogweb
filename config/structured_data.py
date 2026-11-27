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
from main.cases import CASES_PUBLISHED, E3_GITHUB_URL, E3_PYPI_URL, E3_SLUG, SITE_REPO_URL
from main.services import CASES_INDEX_DESCRIPTION

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
    """A case study (main/cases.py, localized) as an article in the page's language, by the person the site is about."""
    url = request.build_absolute_uri(case.url)
    data = {
        '@context': 'https://schema.org',
        '@type': 'Article',
        'headline': case.title,
        'name': case.title,
        'url': url,
        'mainEntityOfPage': url,
        'inLanguage': translation.get_language(),
        'datePublished': CASES_PUBLISHED.isoformat(),
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


def software_source_code(request, case):
    """The open-source package a case is about (the e3 case): its code, its PyPI page and its license."""
    return {
        '@context': 'https://schema.org',
        '@type': 'SoftwareSourceCode',
        'name': case.title,
        'url': E3_PYPI_URL,
        'codeRepository': E3_GITHUB_URL,
        'programmingLanguage': 'Python',
        'license': 'https://opensource.org/license/mit',
        'author': {'@id': person(request)['@id']},
    }


def case_page(request, case):
    """A case's page: the case study (and, for the e3 case, its code), then where it sits: under the cases index."""
    trail = [(_('Home'), reverse('main:index')), (_('Cases'), reverse('main:cases')), (case.title, case.url)]
    data = [case_study(request, case)]
    if case.slug == E3_SLUG:
        data.append(software_source_code(request, case))
    return [*data, breadcrumbs(request, trail)]


def cases_page(request, groups):
    """
    The cases index: a collection of the cases it shows, in the page's order (`groups` is cases.grouped_cases()),
    then where it sits.
    """
    shown = [case for _group, wide, normal in groups for case in [*wide, *normal]]
    url = request.build_absolute_uri(reverse('main:cases'))
    collection = {
        '@context': 'https://schema.org',
        '@type': 'CollectionPage',
        'name': _('What I have built'),
        'description': str(CASES_INDEX_DESCRIPTION),
        'url': url,
        'inLanguage': translation.get_language(),
        'mainEntity': {
            '@type': 'ItemList',
            'itemListElement': [
                {
                    '@type': 'ListItem',
                    'position': position,
                    'url': request.build_absolute_uri(case.url),
                    'name': case.title,
                }
                for position, case in enumerate(shown, start=1)
            ],
        },
    }
    trail = [(_('Home'), reverse('main:index')), (_('Cases'), reverse('main:cases'))]
    return [collection, breadcrumbs(request, trail)]


def area_served():
    """Where he works: his city and country, which the site already names, and remotely."""
    return [
        {'@type': 'City', 'name': settings.OWNER_CITY},
        {'@type': 'Country', 'name': 'Spain', 'identifier': settings.OWNER_COUNTRY},
        'Remote',
    ]


def service(request, localized):
    """A service (main/services.py, localized) in the page's language, offered by the person the site is about."""
    return {
        '@context': 'https://schema.org',
        '@type': 'Service',
        'name': localized.name,
        'serviceType': localized.name,
        'description': localized.description,
        'url': request.build_absolute_uri(localized.url),
        'provider': {'@id': person(request)['@id']},
        'areaServed': area_served(),
    }


def faq_page(request, questions):
    """A page's FAQ: `questions` is the same list of Question the page shows."""
    return {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'url': request.build_absolute_uri(request.path),
        'inLanguage': translation.get_language(),
        'mainEntity': [
            {
                '@type': 'Question',
                'name': str(item.question),
                'acceptedAnswer': {'@type': 'Answer', 'text': str(item.answer)},
            }
            for item in questions
        ],
    }


def service_page(request, localized):
    """A service's page: the service, its FAQ, then where it sits, under the home. There is no services page."""
    faq = [faq_page(request, localized.faq)] if localized.faq else []
    trail = [(_('Home'), reverse('main:index')), (localized.name, localized.url)]
    return [service(request, localized), *faq, breadcrumbs(request, trail)]


def how_i_work_page(request, questions):
    """How I work: its FAQ (`questions`, as the page shows them), then where it sits, under the home."""
    return [
        faq_page(request, questions),
        breadcrumbs(request, [(_('Home'), reverse('main:index')), (_('How I work'), reverse('main:how-i-work'))]),
    ]


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
