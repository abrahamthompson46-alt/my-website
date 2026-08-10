from django.urls import path

from website.views import (
    HomeView,
    PrivacyPolicyView,
    RefundPolicyView,
    SecurityOverviewView,
    StatusPageView,
    TermsOfServiceView,
)

app_name = "website"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("legal/privacy/", PrivacyPolicyView.as_view(), name="privacy"),
    path("legal/terms/", TermsOfServiceView.as_view(), name="terms"),
    path("legal/security/", SecurityOverviewView.as_view(), name="security"),
    path("legal/refund/", RefundPolicyView.as_view(), name="refund"),
    path("status/", StatusPageView.as_view(), name="status"),
]
