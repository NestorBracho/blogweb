from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.translation import gettext as _
from django.views import generic

from blog.models import Category, Post, content_language
from config.forms import HONEYPOT_FIELD

from . import structured_data
from .forms import ContactForm
from .models import ContactRequest

# Posts per page in the home's list, The Binary Journal
HOME_PAGE_SIZE = 4
# Hacker's Haven: the categories with the newest posts, and the latest posts in each
HACKERS_HAVEN_CATEGORIES = 4
HACKERS_HAVEN_POSTS = 5


class HomePostsMixin:
    """The home's list of posts, newest first, a page at a time (?page=)."""

    queryset = Post.objects.filter(is_published=True).select_related('category').order_by('-created')
    paginate_by = HOME_PAGE_SIZE


class IndexView(HomePostsMixin, generic.ListView):
    template_name = 'main/index.html'

    def get_context_data(self, **kwargs):
        kwargs['structured_data'] = structured_data.home_page(self.request)
        # Only queried if the page shows it (many_posts, in config/context_processors.py)
        kwargs['hackers_haven'] = (
            Category.objects.with_published_posts()
            .with_latest_posts(HACKERS_HAVEN_POSTS)
            .order_by('-latest_post')[:HACKERS_HAVEN_CATEGORIES]
        )

        return super().get_context_data(**kwargs)


class MorePostsView(HomePostsMixin, generic.ListView):
    """
    A page of the home's posts and nothing else, for "Load more" to add to the list. Without JavaScript that button
    is a link to the home's own ?page= instead, so nobody lands here.
    """

    template_name = 'main/more_posts.html'

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        # A fragment, not a page: search engines index the home's pages instead
        response.headers['X-Robots-Tag'] = 'noindex'
        return response


class AboutView(generic.TemplateView):
    template_name = 'main/about.html'

    def get_context_data(self, **kwargs):

        kwargs['page_title'] = _('About Me')
        kwargs['meta_description'] = _(
            'Get to know Nestor, a fullstack software engineer passionate about backend '
            'systems, Python, AWS, and technology for social impact. Discover his journey, '
            'skills, and mission to build meaningful digital tools.'
        )

        return super().get_context_data(**kwargs)


class CVView(generic.TemplateView):
    template_name = 'main/cv.html'

    def get_context_data(self, **kwargs):
        kwargs['page_title'] = _('CV')
        kwargs['meta_description'] = _(
            'CV of Nestor Bracho, %(role)s with more than 12 years building web platforms with Python and Django.'
        ) % {'role': settings.OWNER_ROLE}
        kwargs['pdf_url'] = settings.OWNER_CV_PDF_URLS[content_language()]
        kwargs['structured_data'] = structured_data.profile_page(self.request)

        return super().get_context_data(**kwargs)


class PrivacyView(generic.TemplateView):
    template_name = 'main/privacy.html'

    def get_context_data(self, **kwargs):
        kwargs['page_title'] = _('Privacy policy')
        kwargs['meta_description'] = _('What personal data this site collects, why, and how to exercise your rights.')

        return super().get_context_data(**kwargs)


class ContactFormView(generic.CreateView):
    template_name = 'main/contact.html'
    form_class = ContactForm
    model = ContactRequest

    def get_context_data(self, **kwargs):

        kwargs['page_title'] = _('Contact')
        kwargs['meta_description'] = _(
            'Plug into the grid, whether you’re building something bold or need a '
            'sharp mind in the system, this is your uplink to start working together.'
        )
        kwargs['social_image_url'] = static('images/40.jpg')

        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        http_response = super().form_valid(form)
        messages.success(
            self.request,
            _("Your contact request has been successfully submitted. I'll get in touch as soon as possible!"),
        )
        return http_response

    def form_invalid(self, form):
        if form.has_error(HONEYPOT_FIELD):
            # Only bots fill in the hidden field: drop the request without telling them which field gave them away
            messages.error(self.request, _('Something went wrong. Try again later.'))
            return HttpResponseRedirect(self.get_success_url())
        # People get the form back with their text and an error next to each field to fix
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('main:index')
