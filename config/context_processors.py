from django.conf import settings

from blog.models import Post, Category


def owner(request):
    # Personal contact details live in .env so they never end up in the public repo
    return {
        'owner': {
            'email': settings.OWNER_EMAIL,
            'phone': settings.OWNER_PHONE,
            'location': settings.OWNER_LOCATION,
        }
    }


def sidebar(request):
    return {
        'categories': Category.objects.all(),
        'featured_posts': Post.objects.filter(is_published=True).order_by('-created')[:3],
        'recent_posts': Post.objects.filter(is_published=True).order_by('-created')[:3]
    }
