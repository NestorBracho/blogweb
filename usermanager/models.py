from django.db import models

from config.base_models import BaseModel


class NewsletterSubscriber(BaseModel):
    email = models.EmailField(unique=True)
