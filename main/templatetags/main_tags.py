import json

from babel.dates import format_date
from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import translation
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from main import seo

register = template.Library()

# What Django's json_script escapes, so nothing in the data can close the <script> element
JSON_SCRIPT_ESCAPES = {ord('>'): '\\u003E', ord('<'): '\\u003C', ord('&'): '\\u0026'}


@register.filter
def localized_date(value, date_format='dd MMM, yyyy'):
    lang = translation.get_language() or 'en'
    return format_date(value, format=date_format, locale=lang)


@register.filter
def iso8601(value):
    if value:
        return value.isoformat()
    return ''


@register.simple_tag(takes_context=True)
def absolute_uri(context, url):
    # Open Graph and Twitter cards ignore relative URLs. Django renders 500.html without any context, so there is no
    # request to take the domain from: the relative URL is better than a second error.
    request = context.get('request')
    if request is None:
        return url
    return request.build_absolute_uri(url)


@register.simple_tag(takes_context=True)
def page_urls(context):
    return seo.page_urls(context.get('request'))


@register.filter
def open_graph_locale(language):
    return seo.open_graph_locale(language)


@register.simple_tag
def json_ld(data):
    """Schema.org data as a <script type="application/ld+json"> block. Browsers don't run it, so the CSP allows it."""
    content = json.dumps(data, cls=DjangoJSONEncoder).translate(JSON_SCRIPT_ESCAPES)
    return format_html('<script type="application/ld+json">{}</script>', mark_safe(content))
