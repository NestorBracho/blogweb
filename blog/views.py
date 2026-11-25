from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views import generic

from config import structured_data

from . import covers
from .listing import POSTS_PAGE_SIZE
from .models import Category, Post


class LatestPostsMixin:
    """The blog's list of posts, newest first, a page at a time (?page=)."""

    queryset = Post.objects.published().select_related('category').order_by('-published_at')
    paginate_by = POSTS_PAGE_SIZE


class PostListView(LatestPostsMixin, generic.ListView):
    template_name = 'blog/post_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Blog')
        context['meta_description'] = _(
            'Posts by Nestor Bracho on Django, APIs and AI agent-driven development, in English and Spanish.'
        )
        return context


class MorePostsView(LatestPostsMixin, generic.ListView):
    """
    A page of the blog's posts and nothing else, for "Load more" to add to the list. Without JavaScript that button
    is a link to the list's own ?page= instead, so nobody lands here.
    """

    template_name = 'blog/more_posts.html'

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        # A fragment, not a page: search engines index the list's pages instead
        response.headers['X-Robots-Tag'] = 'noindex'
        return response


class PostDetailView(generic.DetailView):
    queryset = Post.objects.published().select_related('category')
    template_name = 'blog/post.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = context['object']
        context['page_title'] = post.title()
        context['meta_description'] = post.description()
        context['og_type'] = 'article'
        context['structured_data'] = structured_data.post_page(self.request, post)
        if post.noindex:
            context['robots'] = 'noindex'
        if post.cover:
            context['social_image_url'] = post.cover_urls['social']
            # Without its social size yet (make_cover_sizes), the original stands in and previews size it themselves
            social_path = post.cover_sizes.get('paths', {}).get('social')
            if social_path:
                context['social_image_size'] = covers.stored_size(post.cover.storage, social_path)
        context.update(self.get_navigation(post))
        return context

    def get_navigation(self, post):
        published = self.get_queryset()
        related = published.filter(category=post.category) if post.category else published.none()
        return {
            'previous_post': published.filter(published_at__lt=post.published_at).order_by('-published_at').first(),
            'next_post': published.filter(published_at__gt=post.published_at).order_by('published_at').first(),
            'related_posts': related.exclude(pk=post.pk).order_by('-published_at')[:3],
        }


class CategoryDetailView(generic.ListView):
    template_name = 'blog/category.html'
    paginate_by = 12

    def get(self, request, *args, **kwargs):
        # Categories without published posts are kept for the future but not shown yet
        self.category = get_object_or_404(Category.objects.with_published_posts(), slug=self.kwargs['slug'])
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.category.posts.published().select_related('category').order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        name = self.category.name()
        context['category'] = self.category
        context['page_title'] = name
        context['meta_description'] = _('Posts about %(category)s by Nestor Bracho.') % {'category': name}
        return context
