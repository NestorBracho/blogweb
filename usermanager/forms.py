from django import forms

from config.forms import HoneypotForm

from .models import NewsletterSubscriber


class NewsletterSubscriberModelForm(HoneypotForm, forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
