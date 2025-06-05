from config import base_models as models


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
