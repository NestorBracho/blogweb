from django.urls import path

from usermanager.views import AddNewsletterSubscriberView, ConfirmSubscriptionView

from .views import AboutView, ContactFormView, CVView, IndexView, PrivacyView

app_name = 'main'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('about/', AboutView.as_view(), name='about'),
    path('cv/', CVView.as_view(), name='cv'),
    path('contact/', ContactFormView.as_view(), name='contact'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
    path('newsletter/', AddNewsletterSubscriberView.as_view(), name='newsletter-subscriber'),
    path('newsletter/confirm/<str:token>/', ConfirmSubscriptionView.as_view(), name='newsletter-confirm'),
]
