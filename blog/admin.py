from django import forms
from django.contrib import admin
from django.db.models import Count

from .models import Category, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name_en', 'name_es', 'parent', 'slug', 'color', 'post_count']
    list_select_related = ['parent']
    search_fields = ['name_en', 'name_es', 'slug']
    prepopulated_fields = {'slug': ['name_en']}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(post_count=Count('posts'))

    @admin.display(description='Posts', ordering='post_count')
    def post_count(self, category):
        return category.post_count


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title_en', 'category', 'is_published', 'kept_out_of_search', 'published_at']
    list_editable = ['is_published']
    list_filter = ['is_published', 'noindex', 'category']
    list_select_related = ['category']
    search_fields = ['title_en', 'title_es', 'slug']
    date_hierarchy = 'published_at'
    # Post.save() builds the slug from the English title, so suggest the same one here
    prepopulated_fields = {'slug': ['title_en']}
    # content_updated is the "Updated" date readers see: it moves only when a title, description or body changes
    readonly_fields = ['read_time', 'created', 'updated', 'content_updated']
    fieldsets = [
        (None, {'fields': ['slug', 'category', 'cover', 'read_time', 'is_published', 'noindex']}),
        ('English', {'fields': ['title_en', 'description_en', 'body_en']}),
        ('Español', {'fields': ['title_es', 'description_es', 'body_es']}),
        ('Dates', {'fields': ['published_at', 'content_updated', 'created', 'updated']}),
    ]

    @admin.display(description='Noindex', boolean=True, ordering='noindex')
    def kept_out_of_search(self, post):
        return bool(post.noindex)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # noindex is nullable only so adding it didn't rebuild the table: here it is a plain checkbox
        if db_field.name == 'noindex':
            return forms.BooleanField(required=False, label='Noindex', help_text=db_field.help_text)
        return super().formfield_for_dbfield(db_field, request, **kwargs)
