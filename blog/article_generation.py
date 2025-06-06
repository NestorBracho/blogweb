import os
import requests
import random
import math
from openai import OpenAI
from django.core.files.base import ContentFile
from django.utils.text import slugify

from .models import Post, Category

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")


def estimate_read_time(text):
    words = len(text.split())
    return math.ceil(words / 200)  # average reading speed ~200 wpm


def get_unsplash_image_url(keyword):
    endpoint = "https://api.unsplash.com/photos/random"
    params = {
        "query": keyword,
        "orientation": "landscape",
        "client_id": UNSPLASH_ACCESS_KEY,
    }
    response = requests.get(endpoint, params=params)
    data = response.json()

    return data["urls"]["regular"]


def generate_article(topic):
    sections = random.randint(3, 6)
    word_target = random.randint(600, 1200)
    category = Category.objects.get(slug='programming')

    prompt = f"""
Generate a blog article in Markdown format about "{topic}". The article should have {sections} sections, 
a clear introduction and a conclusion.
Write it in a human style with natural variation in sentence structure and tone. Target around {word_target} words.
Return only the article body in English, no preamble.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",
             "content": "You are a professional tech writer that explains things clearly and accurately."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
    )

    english_body = response.choices[0].message.content.strip()

    # Translate to Spanish
    translation_prompt = f"Translate the following Markdown article to Spanish:\n\n{english_body}"
    response_es = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",
             "content": "You are a professional tech writer that explains things clearly and accurately."},
            {"role": "user", "content": translation_prompt}
        ],
        temperature=0.7,
    )

    spanish_body = response_es.choices[0].message.content.strip()

    # Get summary and title
    summary_prompt = f"""Summarize the following article in less than 160 characters. Then, provide a short SEO-friendly 
    title (max 60 characters) in both English and Spanish. Markdown format:
    Article:
    {english_body}
    Output format:
    short_description_en: ...
    short_description_es: ...
    title_en: ...
    title_es: ...
    """
    summary_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",
             "content": "You are a professional tech writer that explains things clearly and accurately."},
            {"role": "user", "content": summary_prompt}
        ],
        temperature=0.7,
    )

    lines = summary_response.choices[0].message.content.strip().splitlines()
    short_description_en = lines[0].split(":", 1)[-1].strip()
    title_es = lines[2].split(":", 1)[-1].strip()
    short_description_es = lines[1].split(":", 1)[-1].strip()
    title_en = lines[3].split(":", 1)[-1].strip()
    slug = slugify(title_en)

    post = Post.objects.create(
        slug=slugify(title_en),
        title_es=title_es,
        title_en=title_en,
        body_es=spanish_body,
        body_en=english_body,
        description_es=short_description_es,
        description_en=short_description_en,
        category=category,
        read_time=estimate_read_time(english_body),
    )

    image_prompt = (f"High-quality illustration for a blog post titled: '{title_en}'. The image should represent: "
                    f"{short_description_en}. Professional, modern, engaging.")

    img_response = client.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        n=1,
        quality="hd",
        size="1024x1024"
    )
    filename = f"{slug}_cover.jpg"
    image_url = img_response.data[0].url
    image_response = requests.get(image_url)
    image_content = ContentFile(image_response.content)

    post.cover.save(filename, image_content)
