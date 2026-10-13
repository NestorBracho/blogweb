from django.contrib import admin

from .models import ContactRequest


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'created']
    search_fields = ['name', 'email', 'message']
    date_hierarchy = 'created'
    ordering = ['-created']
    readonly_fields = ['name', 'email', 'message', 'created']

    # Requests only come from the contact form
    def has_add_permission(self, request):
        return False
