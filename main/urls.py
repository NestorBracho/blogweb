from django.urls import path, include
from .views import PostDetailView, CategoryDetailView, ContactFormView
from usermanager.views import AddNewsletterSubscriberView
from django.views.generic import TemplateView

app_name = 'main'
urlpatterns = [
    path('', TemplateView.as_view(template_name='main/index.html'), name='index'),
    path('post/<slug:slug>', PostDetailView.as_view(), name='post-detail'),
    path('tags/<slug:slug>', CategoryDetailView.as_view(), name='category-detail'),
    path('contact', ContactFormView.as_view(), name='contact'),
    path('newsletter/', AddNewsletterSubscriberView.as_view(), name='newsletter-subscriber'),
    path('api/', include('main.api.urls')),
]
