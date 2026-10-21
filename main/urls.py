from django.urls import path

from .views import AboutView, ContactFormView, CVView, IndexView, MorePostsView, PrivacyView

app_name = 'main'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('more-posts/', MorePostsView.as_view(), name='more-posts'),
    path('about/', AboutView.as_view(), name='about'),
    path('cv/', CVView.as_view(), name='cv'),
    path('contact/', ContactFormView.as_view(), name='contact'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
]
