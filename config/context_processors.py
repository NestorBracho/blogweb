import datetime

from django.conf import settings
from django.utils.functional import SimpleLazyObject

from blog.models import Category, Post, content_language
from main.home import HOME_PAGE_SIZE


def years_of_experience():
    """Whole years since his career started, for "more than N years": it started in January, so N is always true."""
    return datetime.date.today().year - settings.OWNER_CAREER_START_YEAR


def owner(request):
    # Personal contact details live in .env so they never end up in the public repo
    return {
        'owner': {
            'role': settings.OWNER_ROLE,
            'email': settings.OWNER_EMAIL,
            'phone': settings.OWNER_PHONE,
            'location': settings.OWNER_LOCATIONS[content_language()],
            'years': years_of_experience(),
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
        # Shown in both the sidebar and the footer: one queryset, so one query per page
        'latest_posts': published.order_by('-created')[:3],
        # While every post fits on the home's first page, the other lists of posts (the sidebar's and Hacker's Haven)
        # would only repeat the same ones, so they wait until there are more. Lazy: only pages with those lists count.
        'many_posts': SimpleLazyObject(lambda: published.count() > HOME_PAGE_SIZE),
    }
