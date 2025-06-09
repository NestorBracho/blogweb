from blog.models import Post, Category


def sidebar(request):
    return {
        'categories': Category.objects.all(),
        'featured_posts': Post.objects.filter(is_published=True).order_by('-created')[:3],
        'recent_posts': Post.objects.filter(is_published=True).order_by('-created')[:3]
    }
