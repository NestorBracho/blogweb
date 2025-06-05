from django import forms

from .models import NewsletterSubscriber


class NewsletterSubscriberModelForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = '__all__'
