from django.urls import path
from .views import ContactFormView
from usermanager.views import AddNewsletterSubscriberView
from django.views.generic import TemplateView

app_name = 'main'
urlpatterns = [
    path('', TemplateView.as_view(template_name='main/index.html'), name='index'),
    path('contact/', ContactFormView.as_view(), name='contact'),
    path('newsletter/', AddNewsletterSubscriberView.as_view(), name='newsletter-subscriber'),
]
