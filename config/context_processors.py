import datetime

from django.conf import settings
from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext_lazy as _

from blog.listing import POSTS_PAGE_SIZE
from blog.models import Category, Post, content_language


def years_of_experience():
    """Whole years since his career started, for "more than N years": it started in January, so N is always true."""
    return datetime.date.today().year - settings.OWNER_CAREER_START_YEAR


# What search results and link previews show for the home and for pages without a description of their own; the
# home's structured data says the same (config/structured_data.py). Written in docs/home-cases.md, at its full length.
SITE_DESCRIPTION = _(
    '%(role)s with more than %(years)s years building web platforms with Python and Django. Three years for the World '
    'Bank Group; now freelance, with AI agent-driven development.'
)


def site_description():
    """The site's description in the active language."""
    return SITE_DESCRIPTION % {'role': settings.OWNER_ROLE, 'years': years_of_experience()}


def owner(request):
    # Personal contact details live in .env so they never end up in the public repo
    return {
        'owner': {
            'role': settings.OWNER_ROLE,
            'email': settings.OWNER_EMAIL,
            'phone': settings.OWNER_PHONE,
            'location': settings.OWNER_LOCATIONS[content_language()],
            'years': years_of_experience(),
            'description': site_description(),
            'github_url': settings.OWNER_GITHUB_URL,
            'linkedin_url': settings.OWNER_LINKEDIN_URL,
        }
    }


def newsletter(request):
    return {'newsletter_enabled': settings.NEWSLETTER_ENABLED}


def sidebar(request):
    published = Post.objects.published()
    return {
        'categories': Category.objects.with_published_posts().order_by('-latest_post'),
        # Shown in the blog's sidebar and footer, and in the home's "From the blog": one queryset, so one query per page
        'latest_posts': published.order_by('-published_at')[:3],
        # While every post fits on the blog's first page, the sidebar's list of posts would only repeat the same ones,
        # so it waits until there are more. Lazy: only pages with that list count.
        'many_posts': SimpleLazyObject(lambda: published.count() > POSTS_PAGE_SIZE),
    }
