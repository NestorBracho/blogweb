from django import forms

from config.forms import HoneypotForm


class SubscribeForm(HoneypotForm):
    email = forms.EmailField()
