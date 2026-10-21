import logging
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.core import signing
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views import generic

from config.throttling import FormThrottle

from .forms import SubscribeForm
from .models import NewsletterSubscriber

logger = logging.getLogger(__name__)

CONFIRMATION_LINK_MAX_AGE = timedelta(days=7)
# Pending addresses get the link again when they subscribe again, but not more often than this
CONFIRMATION_RESEND_COOLDOWN = timedelta(hours=1)


class AddNewsletterSubscriberView(generic.FormView):
    form_class = SubscribeForm
    http_method_names = ['post']

    def form_valid(self, form):
        # Before looking the address up, so the answer says nothing about it
        if not FormThrottle('newsletter').allow_request(self.request, self):
            messages.error(
                self.request, _("You've tried to subscribe several times in a short time. Please try again later.")
            )
            return HttpResponseRedirect(self.get_success_url())

        subscriber, _created = NewsletterSubscriber.objects.get_or_create(email=form.cleaned_data['email'].lower())
        if subscriber.claim_confirmation_email(CONFIRMATION_RESEND_COOLDOWN):
            try:
                send_confirmation_email(self.request, subscriber)
            except OSError:
                logger.exception('Could not send the newsletter confirmation email')
                # Nothing went out, so trying again mustn't wait for the cooldown
                NewsletterSubscriber.objects.filter(pk=subscriber.pk).update(confirmation_sent_at=None)
                messages.error(self.request, _("We couldn't send you the confirmation email. Please try again later."))
                return HttpResponseRedirect(self.get_success_url())

        # Same answer for new, pending and confirmed addresses, emailed or not, so nobody can find out who is subscribed
        messages.success(self.request, _('Almost there! Check your inbox and confirm your subscription.'))
        return HttpResponseRedirect(self.get_success_url())

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
        return reverse('main:index')


class ConfirmSubscriptionView(generic.View):
    def get(self, request, token):
        try:
            subscriber = NewsletterSubscriber.from_confirmation_token(token, max_age=CONFIRMATION_LINK_MAX_AGE)
        except (signing.BadSignature, NewsletterSubscriber.DoesNotExist):
            messages.error(
                request, _('This confirmation link is invalid or has expired. Subscribe again to get a new one.')
            )
        else:
            subscriber.confirm()
            messages.success(request, _('Your subscription is confirmed. Thank you!'))
        return redirect('main:index')


def send_confirmation_email(request, subscriber):
    context = {
        'confirm_url': request.build_absolute_uri(
            reverse('usermanager:newsletter-confirm', args=[subscriber.confirmation_token()])
        ),
        'days': CONFIRMATION_LINK_MAX_AGE.days,
        'site_url': request.build_absolute_uri(reverse('main:index')),
    }
    send_mail(
        subject=_('Confirm your subscription to Bracho'),
        message=render_to_string('usermanager/email/confirm_subscription.txt', context, request=request),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[subscriber.email],
    )
