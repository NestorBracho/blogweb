from django import template
from babel.dates import format_date
from django.utils import translation

register = template.Library()


@register.filter
def localized_date(value, date_format="dd MMM, yyyy"):
    lang = translation.get_language() or 'en'
    return format_date(value, format=date_format, locale=lang)


@register.filter
def iso8601(value):
    if value:
        return value.isoformat()
    return ""
