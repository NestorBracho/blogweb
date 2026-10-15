from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views import generic

from .models import Category, Post


class PostDetailView(generic.DetailView):
    queryset = Post.objects.filter(is_published=True).select_related('category')
    template_name = 'blog/post.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = context['object']
        context['page_title'] = post.title()
        context['meta_description'] = post.description()
        if post.cover:
            context['social_image_url'] = post.cover_urls['social']
        context.update(self.get_navigation(post))
        return context

    def get_navigation(self, post):
        published = self.get_queryset()
        related = published.filter(category=post.category) if post.category else published.none()
        return {
            'previous_post': published.filter(created__lt=post.created).order_by('-created').first(),
            'next_post': published.filter(created__gt=post.created).order_by('created').first(),
            'related_posts': related.exclude(pk=post.pk).order_by('-created')[:3],
        }


class CategoryDetailView(generic.ListView):
    template_name = 'blog/category.html'
    paginate_by = 12

    def get(self, request, *args, **kwargs):
        # Categories without published posts are kept for the future but not shown yet
        self.category = get_object_or_404(Category.objects.with_published_posts(), slug=self.kwargs['slug'])
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.category.posts.filter(is_published=True).select_related('category').order_by('-created')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        name = self.category.name()
        context['category'] = self.category
        context['page_title'] = name
        context['meta_description'] = _('Posts about %(category)s by Nestor Bracho.') % {'category': name}
        return context
