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
            context['social_image_url'] = post.cover.url
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
    queryset = Post.objects.filter(is_published=True).order_by('-created')
    template_name = 'blog/category.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):

        kwargs['page_title'] = _('Categories')
        kwargs['meta_description'] = ''
        kwargs['social_image_url'] = ''

        if self.object:
            kwargs['category'] = self.object
        return super().get_context_data(*args, **kwargs)

    def get_queryset(self):
        category = self.object
        queryset = self.queryset.filter(category=category)

        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        return queryset

    def get_object(self):
        # Categories without published posts are kept for the future but not shown yet
        return get_object_or_404(Category.objects.with_published_posts(), slug=self.kwargs['slug'])
