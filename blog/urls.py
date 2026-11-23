from django.urls import path

from .feeds import LatestPostsFeed
from .views import CategoryDetailView, MorePostsView, PostDetailView, PostListView

app_name = 'blog'
urlpatterns = [
    path('blog/', PostListView.as_view(), name='post-list'),
    path('blog/more/', MorePostsView.as_view(), name='more-posts'),
    path('post/<slug:slug>', PostDetailView.as_view(), name='post-detail'),
    path('tags/<slug:slug>', CategoryDetailView.as_view(), name='category-detail'),
    path('feed.xml', LatestPostsFeed(), name='feed'),
]
