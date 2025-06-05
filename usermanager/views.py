from django.views import generic
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _

from .froms import NewsletterSubscriberModelForm


class AddNewsletterSubscriberView(generic.CreateView):
    form_class = NewsletterSubscriberModelForm

    def form_valid(self, form):
        messages.success(self.request, _("You have been subscribed to your newsletter!"))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("You've not been subscribed to your newsletter. Something went wrong."))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if not next_url:
            next_url = self.request.META.get('HTTP_REFERER')
        return next_url or '/'
