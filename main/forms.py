from django import forms
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import ContactRequest


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = ('name', 'email', 'message')

    def save(self, commit=True):
        instance = super(ContactForm, self).save(commit)
        self.send_mail(
            context={
                'name': self.cleaned_data['name'],
                'email': self.cleaned_data['email'],
                'message': self.cleaned_data['message'],
            },
            subject='New Contact Request from the Blog!',
            from_email=settings.EMAIL_HOST_USER,
            to_email=settings.EMAIL_HOST_USER
        )
        return instance

    def send_mail(self, context, from_email, to_email, subject, html_email_template_name='main/email/contact.html'):
        html_content = render_to_string(html_email_template_name, context)

        email_msg = EmailMultiAlternatives(subject, '', from_email, [to_email])
        email_msg.attach_alternative(html_content, "text/html")

        email_msg.send()
