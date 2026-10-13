from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.translation import gettext as _
from django.views import generic

from .forms import ContactForm
from .models import ContactRequest


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
        kwargs['social_image_url'] = static('images/40.png')

        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        http_response = super().form_valid(form)
        messages.success(
            self.request,
            _("Your contact request has been successfully submitted. I'll get in touch as soon as possible!"),
        )
        return http_response

    def form_invalid(self, form):
        messages.error(self.request, _('Something went wrong. Try again latter.'))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('main:index')
