from django.core import signing
from django.db import models
from django.utils import timezone

from config.base_models import BaseModel

CONFIRMATION_SALT = 'usermanager.newsletter.confirm'


class NewsletterSubscriber(BaseModel):
    email = models.EmailField(unique=True)
    # Double opt-in: only addresses confirmed through the emailed link may receive the newsletter
    confirmed_at = models.DateTimeField(null=True, blank=True)
    # When the link was last emailed, so the form can't be used to flood someone else's inbox
    confirmation_sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email

    def confirmation_token(self):
        return signing.dumps(str(self.pk), salt=CONFIRMATION_SALT)

    @classmethod
    def from_confirmation_token(cls, token, max_age):
        """Raises signing.BadSignature (expired or tampered tokens included) or DoesNotExist."""
        return cls.objects.get(pk=signing.loads(token, salt=CONFIRMATION_SALT, max_age=max_age))

    def claim_confirmation_email(self, cooldown):
        """
        Records that the confirmation link is being emailed now, unless the address is confirmed or got it less than
        `cooldown` ago, and says whether to send it. A single UPDATE, so requests at the same time can't both send it.
        """
        now = timezone.now()
        pending = NewsletterSubscriber.objects.filter(pk=self.pk, confirmed_at=None)
        return bool(pending.exclude(confirmation_sent_at__gt=now - cooldown).update(confirmation_sent_at=now))

    def confirm(self):
        if self.confirmed_at is None:
            self.confirmed_at = timezone.now()
            self.save(update_fields=['confirmed_at', 'updated'])
