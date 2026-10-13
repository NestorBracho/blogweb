from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views import generic

from .froms import NewsletterSubscriberModelForm


class AddNewsletterSubscriberView(generic.CreateView):
    form_class = NewsletterSubscriberModelForm

    def form_valid(self, form):
        messages.success(self.request, _("You've subscribed to my newsletter!"))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('We were unable to subscribe you to your newsletter. Something went wrong.'))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if not next_url:
            next_url = self.request.META.get('HTTP_REFERER')
        # Only redirect back to our own site
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={self.request.get_host()}, require_https=self.request.is_secure()
        ):
            return next_url
        return '/'
