"""Post bodies: Markdown in, HTML that is safe to put on the page out."""

import markdown
import nh3
from django.utils.safestring import mark_safe
from markdown.extensions import admonition, attr_list, codehilite, fenced_code, tables

# Bodies come from the admin, the API and draft_article (an LLM), and Markdown passes raw HTML through, so the
# rendered HTML is cleaned before it reaches the page. nh3's defaults keep the usual formatting tags and drop scripts,
# event handlers and `javascript:` links; on top of them, posts need classes (highlighted code, admonitions and
# `{: .class}`) and the alignment of table columns. Anything else, such as an <iframe>, is removed.
ATTRIBUTES = {
    **nh3.ALLOWED_ATTRIBUTES,
    '*': {'class', 'lang', 'title'},
    'th': nh3.ALLOWED_ATTRIBUTES['th'] | {'style'},
    'td': nh3.ALLOWED_ATTRIBUTES['td'] | {'style'},
}

sanitizer = nh3.Cleaner(attributes=ATTRIBUTES, filter_style_properties={'text-align'})


def render_markdown(text):
    html = markdown.markdown(
        text,
        extensions=[
            fenced_code.FencedCodeExtension(),
            codehilite.CodeHiliteExtension(css_class='highlight'),
            admonition.AdmonitionExtension(),
            attr_list.AttrListExtension(),
            tables.TableExtension(),
        ],
    )
    return mark_safe(sanitizer.clean(html))
