from django.db import models

from config.base_models import BaseModel


class ContactRequest(BaseModel):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
