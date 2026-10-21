"""AI-assisted drafting: turn a topic into an unpublished, bilingual post for the author to review and edit."""

import base64

from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import CharField
from django.utils.text import Truncator
from openai import OpenAI
from openai.types.responses import ParsedResponse
from pydantic import BaseModel, Field, ValidationError

from .models import Category, Post

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


def write_article(client: OpenAI, topic: str) -> ArticleDraft:
    try:
        response = client.responses.parse(
            model=settings.OPENAI_MODEL,
            instructions=SYSTEM_PROMPT,
            input=ARTICLE_PROMPT.format(topic=topic),
            text_format=ArticleDraft,
            # The draft is kept here, in the database; the Responses API would also keep a copy at OpenAI by default
            store=False,
        )
    except ValidationError as error:
        # The SDK parses the answer into ArticleDraft itself; one cut short (by a length limit or a filter) fails
        raise DraftingError('the model returned an incomplete article') from error
    draft = response.output_parsed
    if draft is None:
        raise DraftingError(refusal(response) or 'the model returned no article')
    return draft


def refusal(response: ParsedResponse[ArticleDraft]) -> str | None:
    """The model's reason for declining to write the article, which it gives instead of the structured answer."""
    for item in response.output:
        if item.type == 'message':
            for content in item.content:
                if content.type == 'refusal':
                    return content.refusal
    return None


def save_draft(draft: ArticleDraft, category: Category) -> Post:
    return Post.objects.create(
        title_en=fit_column(draft.title_en, 'title_en'),
        title_es=fit_column(draft.title_es, 'title_es'),
        description_en=fit_column(draft.description_en, 'description_en'),
        description_es=fit_column(draft.description_es, 'description_es'),
        body_en=draft.body_en,
        body_es=draft.body_es,
        category=category,
        is_published=False,
    )


def fit_column(text: str, field_name: str) -> str:
    # The limits are in the schema descriptions, but the model can still overshoot the database columns
    field = Post._meta.get_field(field_name)
    return Truncator(text).chars(field.max_length) if isinstance(field, CharField) and field.max_length else text


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
