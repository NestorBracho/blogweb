from django.views import generic
from django.shortcuts import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.templatetags.static import static
from django.utils.translation import gettext as _

from .models import ContactRequest
from .forms import ContactForm


class ContactFormView(generic.CreateView):
    template_name = 'main/contact.html'
    form_class = ContactForm
    model = ContactRequest

    def get_context_data(self, **kwargs):

        kwargs['page_title'] = _('Contact')
        kwargs['meta_description'] = _('Plug into the grid, whether you’re building something bold or need a '
                                       'sharp mind in the system, this is your uplink to start working together.')
        kwargs['social_image_url'] = static('images/40.png')

        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        print('Valid')
        http_response = super().form_valid(form)
        messages.success(self.request, _("Your contact request has been successfully submitted. "
                                         "I'll get in touch as soon as possible!"))
        return http_response

    def form_invalid(self, form):
        print('INvalid')
        print('----')
        print(form.errors)
        messages.error(self.request, _("Something went wrong. Try again latter."))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('main:index')
