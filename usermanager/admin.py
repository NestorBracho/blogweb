from django.contrib import admin

from .models import NewsletterSubscriber


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'confirmed_at', 'created']
    list_filter = [('confirmed_at', admin.EmptyFieldListFilter)]
    search_fields = ['email']
    ordering = ['-created']
