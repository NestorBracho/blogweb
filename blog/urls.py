from django.urls import path

from .feeds import LatestPostsFeed
from .views import CategoryDetailView, PostDetailView

app_name = 'blog'
urlpatterns = [
    path('post/<slug:slug>', PostDetailView.as_view(), name='post-detail'),
    path('tags/<slug:slug>', CategoryDetailView.as_view(), name='category-detail'),
    path('feed.xml', LatestPostsFeed(), name='feed'),
]
