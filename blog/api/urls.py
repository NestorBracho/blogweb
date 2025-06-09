from django.urls import path
from blog.api import views

app_name = 'api'
urlpatterns = [
    path('search/<str:query>', views.SearchPostAPIView.as_view(), name='search'),
    path('post/', views.CreateArticleAPIView.as_view(), name='create-post'),
]
