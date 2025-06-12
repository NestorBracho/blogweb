from django.urls import path
from rest_framework.routers import DefaultRouter
from blog.api import views

router = DefaultRouter()
router.register(r'post', views.PostModelViewSet, basename='post')

app_name = 'api'
urlpatterns = [
    # path('search/<str:query>', views.SearchPostAPIView.as_view(), name='search'),
] + router.urls
