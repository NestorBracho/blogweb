from django.contrib import admin
from django.db.models import Count

from .models import Category, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name_en', 'name_es', 'slug', 'color', 'post_count']
    search_fields = ['name_en', 'name_es', 'slug']
    prepopulated_fields = {'slug': ['name_en']}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(post_count=Count('posts'))

    @admin.display(description='Posts', ordering='post_count')
    def post_count(self, category):
        return category.post_count


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title_en', 'category', 'is_published', 'created']
    list_editable = ['is_published']
    list_filter = ['is_published', 'category']
    list_select_related = ['category']
    search_fields = ['title_en', 'title_es', 'slug']
    date_hierarchy = 'created'
    # Post.save() builds the slug from the English title, so suggest the same one here
    prepopulated_fields = {'slug': ['title_en']}
    readonly_fields = ['created', 'updated']
    fieldsets = [
        (None, {'fields': ['slug', 'category', 'cover', 'read_time', 'is_published']}),
        ('English', {'fields': ['title_en', 'description_en', 'body_en']}),
        ('Español', {'fields': ['title_es', 'description_es', 'body_es']}),
        ('Dates', {'fields': ['created', 'updated']}),
    ]
