from django.db.models import Q
from rest_framework import generics

from blog.models import Post
from .serializers import PostSerializer, CreatePostSerializer


class SearchPostAPIView(generics.ListAPIView):
    queryset = Post.objects.filter(is_published=True)
    serializer_class = PostSerializer
    pagination_class = None

    def filter_queryset(self, queryset):

        lang = self.request.headers.get('X-Language')
        query_string = self.kwargs.get('query')

        if lang == 'es':
            queryset = queryset.filter(
                Q(title_es__icontains=query_string) |
                Q(description_es__icontains=query_string) |
                Q(body_es__icontains=query_string) |
                Q(category__name_es__contains=query_string)
            )
        else:
            queryset = queryset.filter(
                Q(title_en__icontains=query_string) |
                Q(description_en__icontains=query_string) |
                Q(body_en__icontains=query_string) |
                Q(category__name_en__contains=query_string)
            )

        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset


class CreateArticleAPIView(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = CreatePostSerializer

