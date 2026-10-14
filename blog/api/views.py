from django.conf import settings
from django.utils import translation
from django.utils.cache import patch_vary_headers
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView

from blog.models import Category, Post, content_language

from .serializers import CategorySerializer, CreatePostSerializer, SearchPostSerializer


class LanguageHeaderMixin:
    """Lets clients pick the language with an `X-Language: en|es` header; otherwise Django's detection applies."""

    def initial(self, request, *args, **kwargs):
        language = request.headers.get('X-Language')
        if language in dict(settings.LANGUAGES):
            translation.activate(language)
        super().initial(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        patch_vary_headers(response, ['X-Language'])
        return response


class PostModelViewSet(LanguageHeaderMixin, viewsets.ModelViewSet):
    queryset = Post.objects.filter(is_published=True).select_related('category').order_by('-created')
    filter_backends = [SearchFilter]
    write_serializer_class = CreatePostSerializer
    read_serializer_class = SearchPostSerializer

    @property
    def search_fields(self):
        # Search the content in the language being read
        language = content_language()
        return [f'title_{language}', f'description_{language}', f'body_{language}', f'category__name_{language}']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return self.write_serializer_class
        return self.read_serializer_class


class CategoryModelListAPIView(LanguageHeaderMixin, ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.with_published_posts().order_by('-latest_post')[:4]
