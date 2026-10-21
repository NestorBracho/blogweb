from django.conf import settings
from django.utils import translation
from django.utils.cache import patch_vary_headers
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView

from blog.models import Category, Post, content_language

from .serializers import CategoryWithPostsSerializer, PostDetailSerializer, PostListSerializer, PostWriteSerializer


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
    queryset = Post.objects.select_related('category').order_by('-created')
    filter_backends = [SearchFilter]

    def get_queryset(self):
        # The list feeds the site's search, so it only ever shows published posts, even to staff signed in to the
        # admin. Staff can read, edit, publish or delete any post, drafts included, by its id.
        queryset = super().get_queryset()
        if self.action == 'list' or not self.request.user.is_staff:
            return queryset.filter(is_published=True)
        return queryset

    @property
    def search_fields(self):
        # Search the content in the language being read
        language = content_language()
        return [f'title_{language}', f'description_{language}', f'body_{language}', f'category__name_{language}']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PostWriteSerializer
        if self.action == 'retrieve':
            return PostDetailSerializer
        return PostListSerializer


class CategoryModelListAPIView(LanguageHeaderMixin, ListAPIView):
    """The four most recently active categories, each with its five latest posts."""

    serializer_class = CategoryWithPostsSerializer

    def get_queryset(self):
        return Category.objects.with_published_posts().with_latest_posts(5).order_by('-latest_post')[:4]
