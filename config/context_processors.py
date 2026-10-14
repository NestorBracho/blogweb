from django.conf import settings

from blog.models import Category, Post


def owner(request):
    # Personal contact details live in .env so they never end up in the public repo
    return {
        'owner': {
            'email': settings.OWNER_EMAIL,
            'phone': settings.OWNER_PHONE,
            'location': settings.OWNER_LOCATION,
            'github_url': settings.OWNER_GITHUB_URL,
            'linkedin_url': settings.OWNER_LINKEDIN_URL,
        }
    }


def sidebar(request):
    return {
        'categories': Category.objects.with_published_posts().order_by('-latest_post'),
        'featured_posts': Post.objects.filter(is_published=True).order_by('-created')[:3],
        'recent_posts': Post.objects.filter(is_published=True).order_by('-created')[:3],
    }
