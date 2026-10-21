from django.urls import path

from .views import AddNewsletterSubscriberView, ConfirmSubscriptionView

app_name = 'usermanager'
urlpatterns = [
    path('newsletter/', AddNewsletterSubscriberView.as_view(), name='newsletter-subscriber'),
    # Confirmation emails already sent link here: the address must not change
    path('newsletter/confirm/<str:token>/', ConfirmSubscriptionView.as_view(), name='newsletter-confirm'),
]
