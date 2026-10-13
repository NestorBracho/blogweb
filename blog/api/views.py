from django.conf import settings
from django.db.models import Max, Q
from django.utils import translation
from django.utils.cache import patch_vary_headers
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from blog.models import Category, Post

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
    write_serializer_class = CreatePostSerializer
    read_serializer_class = SearchPostSerializer

    def list(self, request, *args, **kwargs):
        if 'search' in request.GET:
            queryset = self._search_filter_queryset(self.get_queryset())
        else:
            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return self.write_serializer_class
        return self.read_serializer_class

    def _search_filter_queryset(self, queryset):

        lang = self.request.headers.get('X-Language')
        query_string = self.request.GET.get('search')

        if query_string == '':
            return queryset.none()

        if lang == 'es':
            queryset = queryset.filter(
                Q(title_es__icontains=query_string)
                | Q(description_es__icontains=query_string)
                | Q(body_es__icontains=query_string)
                | Q(category__name_es__contains=query_string)
            )
        else:
            queryset = queryset.filter(
                Q(title_en__icontains=query_string)
                | Q(description_en__icontains=query_string)
                | Q(body_en__icontains=query_string)
                | Q(category__name_en__contains=query_string)
            )

        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)

        return queryset


class CategoryModelListAPIView(LanguageHeaderMixin, ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        return (
            self.queryset.annotate(latest_post_created=Max('posts__created'))
            .filter(latest_post_created__isnull=False)
            .order_by('-latest_post_created')[:4]
        )
