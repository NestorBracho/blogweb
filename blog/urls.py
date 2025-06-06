from django.urls import path, include
from .views import PostDetailView, CategoryDetailView

app_name = 'blog'
urlpatterns = [
    path('post/<slug:slug>', PostDetailView.as_view(), name='post-detail'),
    path('tags/<slug:slug>', CategoryDetailView.as_view(), name='category-detail'),
    path('api/', include('blog.api.urls')),
]
