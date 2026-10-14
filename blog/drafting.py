"""AI-assisted drafting: turn a topic into an unpublished, bilingual post for the author to review and edit."""

import base64

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.text import Truncator
from pydantic import BaseModel, Field

from .models import Post

SYSTEM_PROMPT = (
    'You write drafts for a personal technical blog published in English and Spanish. '
    'Explain things clearly and accurately, and say so when something is uncertain.'
)

ARTICLE_PROMPT = (
    'Write a blog article about "{topic}" of around 1,000 words, with an introduction, three to six sections and '
    'a conclusion. Use Markdown with ## headings, and fenced code blocks where they help. Then give the title, '
    'summary and article in Spanish too.'
)


class ArticleDraft(BaseModel):
    """Shape of the model's answer; the OpenAI SDK turns it into a JSON schema and parses the reply into it."""

    title_en: str = Field(description='Title for search engines, at most 60 characters')
    title_es: str = Field(description='The title in Spanish, at most 60 characters')
    description_en: str = Field(description='Summary for search results, at most 160 characters')
    description_es: str = Field(description='The summary in Spanish, at most 160 characters')
    body_en: str = Field(description='The article in Markdown, without a top-level heading')
    body_es: str = Field(description='The article in Spanish, in Markdown, without a top-level heading')


class DraftingError(Exception):
    pass


def write_article(client, topic):
    completion = client.beta.chat.completions.parse(
        model=settings.OPENAI_MODEL,
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': ARTICLE_PROMPT.format(topic=topic)},
        ],
        response_format=ArticleDraft,
    )
    message = completion.choices[0].message
    if message.parsed is None:
        raise DraftingError(message.refusal or 'the model returned no article')
    return message.parsed


def save_draft(draft, category):
    # The limits are in the schema descriptions, but the model can still overshoot the database columns
    title_length = Post._meta.get_field('title_en').max_length
    description_length = Post._meta.get_field('description_en').max_length
    return Post.objects.create(
        title_en=Truncator(draft.title_en).chars(title_length),
        title_es=Truncator(draft.title_es).chars(title_length),
        description_en=Truncator(draft.description_en).chars(description_length),
        description_es=Truncator(draft.description_es).chars(description_length),
        body_en=draft.body_en,
        body_es=draft.body_es,
        category=category,
        is_published=False,
    )


def generate_cover(client, post):
    image = client.images.generate(
        model='dall-e-3',
        prompt=(
            f'Editorial illustration for a technology blog post titled "{post.title_en}": {post.description_en}. '
            'Modern and clean, without any text.'
        ),
        quality='hd',
        size='1024x1024',
        response_format='b64_json',
    )
    post.cover.save(f'{post.slug}.png', ContentFile(base64.b64decode(image.data[0].b64_json)))
