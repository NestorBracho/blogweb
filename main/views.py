from django.views import generic
from django.utils import translation
from django.utils.translation import gettext as _
from django.http import Http404

from .forms import ContactForm
from .models import Post, Category


class PostDetailView(generic.DetailView):
    queryset = Post.objects.all()
    template_name = 'main/post.html'

    page_title = None
    meta_description = None
    social_image_url = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = translation.get_language()
        if lang == 'en':
            context['page_title'] = context['object'].title_en
            context['meta_description'] = context['object'].description_en
        else:
            context['page_title'] = context['object'].title_es
            context['meta_description'] = context['object'].description_es
        self.social_image_url = self.request.build_absolute_uri(context['object'].cover.url)
        return context


class CategoryDetailView(generic.ListView):
    queryset = Post.objects.all()
    template_name = 'main/category.html'

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


class ContactFormView(generic.FormView):
    template_name = 'main/contact.html'
    form_class = ContactForm

    def get_context_data(self, **kwargs):

        kwargs['page_title'] = _('Contact')
        kwargs['meta_description'] = ''
        kwargs['social_image_url'] = ''

        return super().get_context_data(**kwargs)

