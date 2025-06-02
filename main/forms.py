from django import forms


class ContactForm(forms.Form):
    name = forms.CharField()
    reply_to = forms.EmailField()
    message = forms.CharField()
