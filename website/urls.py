from django.urls import path

from website.views import (
    ArchitectureView,
    ChurchesSolutionView,
    ContinuityView,
    EducationSolutionView,
    EnterprisesSolutionView,
    EnterpriseReadinessView,
    HealthcareSolutionView,
    HomeView,
    IntegrationsView,
    MicrofinanceSolutionView,
    OnboardingView,
    OutboundIntentRedirectView,
    PaymentsPlatformView,
    PrivacyCenterView,
    PrivacyPolicyView,
    RefundPolicyView,
    SecurityOverviewView,
    SLAView,
    StatusPageView,
    TermsOfServiceView,
)

app_name = "website"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path(
        "go/<slug:slug>/<str:intent>/",
        OutboundIntentRedirectView.as_view(),
        name="outbound_intent",
    ),
    path("solutions/churches/", ChurchesSolutionView.as_view(), name="solution_churches"),
    path("solutions/microfinance/", MicrofinanceSolutionView.as_view(), name="solution_microfinance"),
    path("solutions/enterprises/", EnterprisesSolutionView.as_view(), name="solution_enterprises"),
    path("solutions/education/", EducationSolutionView.as_view(), name="solution_education"),
    path("solutions/healthcare/", HealthcareSolutionView.as_view(), name="solution_healthcare"),
    path("platform/architecture/", ArchitectureView.as_view(), name="architecture"),
    path("platform/payments/", PaymentsPlatformView.as_view(), name="payments_platform"),
    path("platform/integrations/", IntegrationsView.as_view(), name="integrations"),
    path("platform/sla/", SLAView.as_view(), name="sla"),
    path("platform/onboarding/", OnboardingView.as_view(), name="onboarding"),
    path("platform/privacy/", PrivacyCenterView.as_view(), name="privacy_center"),
    path("platform/continuity/", ContinuityView.as_view(), name="continuity"),
    path("legal/privacy/", PrivacyPolicyView.as_view(), name="privacy"),
    path("legal/terms/", TermsOfServiceView.as_view(), name="terms"),
    path("legal/security/", SecurityOverviewView.as_view(), name="security"),
    path("legal/enterprise/", EnterpriseReadinessView.as_view(), name="enterprise"),
    path("legal/refund/", RefundPolicyView.as_view(), name="refund"),
    path("status/", StatusPageView.as_view(), name="status"),
]
