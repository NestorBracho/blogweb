from django.urls import path
from main.api import views

app_name = 'api'
urlpatterns = [
    path('search/<str:query>', views.SearchPostAPIView.as_view(), name='search'),
]
