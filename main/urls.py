from django.urls import path
from django.views.generic import RedirectView

from .views import (
    AboutView,
    CaseDetailView,
    CasesView,
    ContactFormView,
    CVView,
    HowIWorkView,
    IndexView,
    PrivacyView,
    ServiceDetailView,
)

app_name = 'main'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    # "Load more" asked here while the home listed the posts; a page open since then still does
    path('more-posts/', RedirectView.as_view(pattern_name='blog:more-posts', permanent=True, query_string=True)),
    path('cases/', CasesView.as_view(), name='cases'),
    path('cases/<slug:slug>/', CaseDetailView.as_view(), name='case-detail'),
    path('services/<slug:slug>/', ServiceDetailView.as_view(), name='service-detail'),
    path('how-i-work/', HowIWorkView.as_view(), name='how-i-work'),
    path('about/', AboutView.as_view(), name='about'),
    path('cv/', CVView.as_view(), name='cv'),
    path('contact/', ContactFormView.as_view(), name='contact'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
]
