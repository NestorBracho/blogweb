from django import forms

HONEYPOT_FIELD = 'contact_me_by_fax_only'


class HoneypotForm(forms.Form):
    """Adds a field people never see (templates/lib/_honeypot_field.html hides it) and bots tend to fill in."""

    contact_me_by_fax_only = forms.CharField(required=False)

    def clean_contact_me_by_fax_only(self):
        if self.cleaned_data[HONEYPOT_FIELD]:
            raise forms.ValidationError('Filled in a field that is hidden from people.', code='honeypot')
        return ''
