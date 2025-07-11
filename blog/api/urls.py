from django.urls import path
from rest_framework.routers import DefaultRouter
from blog.api import views

router = DefaultRouter()
router.register(r'post', views.PostModelViewSet, basename='post')

app_name = 'api'
urlpatterns = [
    path('categories', views.CategoryModelListAPIView.as_view(), name='categories'),
] + router.urls
