from blog.models import Post, Category


def sidebar(request):
    return {
        'categories': Category.objects.all(),
        'featured_posts': Post.objects.all().order_by('-created')[:3],
        'recent_posts': Post.objects.all().order_by('-created')[:3]
    }
