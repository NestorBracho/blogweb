from django.views import generic
from django.utils import translation
from django.utils.translation import gettext as _
from django.http import Http404

from .models import Post, Category


class PostDetailView(generic.DetailView):
    queryset = Post.objects.filter(is_published=True).select_related('category')
    template_name = 'blog/post.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = context['object']
        lang = translation.get_language()
        if lang == 'en':
            context['page_title'] = post.title_en
            context['meta_description'] = post.description_en
        else:
            context['page_title'] = post.title_es
            context['meta_description'] = post.description_es
        if post.cover:
            context['social_image_url'] = post.cover.url
        return context


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
            kwargs["category"] = self.object
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
        queryset = Category.objects.all()

        slug = self.kwargs.get('slug')
        queryset = queryset.filter(slug=slug)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": queryset.model._meta.verbose_name}
            )
        return obj
