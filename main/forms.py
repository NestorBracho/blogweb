import logging

from django import forms
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import ContactRequest

logger = logging.getLogger(__name__)


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = ('name', 'email', 'message')

    def save(self, commit=True):
        instance = super(ContactForm, self).save(commit)
        try:
            self.send_mail(
                context={
                    'name': self.cleaned_data['name'],
                    'email': self.cleaned_data['email'],
                    'message': self.cleaned_data['message'],
                },
                subject='New Contact Request from the Blog!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_email=settings.CONTACT_EMAIL,
                reply_to=self.cleaned_data['email'],
            )
        except Exception:
            # The request is already stored in the DB and visible in the admin
            logger.exception('Could not send contact request email')
        return instance

    def send_mail(self, context, from_email, to_email, subject, reply_to=None,
                  html_email_template_name='main/email/contact.html'):
        html_content = render_to_string(html_email_template_name, context)
        text_content = '{name} <{email}>\n\n{message}'.format(**context)

        email_msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email],
                                           reply_to=[reply_to] if reply_to else None)
        email_msg.attach_alternative(html_content, "text/html")

        email_msg.send()
