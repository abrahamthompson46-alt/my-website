from django.urls import path

from operations.action_views import (
    DemoRequestUpdateView,
    ManualPaymentConfirmView,
    SupportTicketUpdateView,
)
from operations.views import (
    ActivityLogsView,
    AnalyticsView,
    CustomersView,
    DashboardView,
    DemoRequestsView,
    DocumentationView,
    LeadsView,
    MarketingView,
    PaymentsView,
    ProductsView,
    SupportView,
    SystemHealthView,
)

app_name = "operations"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("products/", ProductsView.as_view(), name="products"),
    path("customers/", CustomersView.as_view(), name="customers"),
    path("leads/", LeadsView.as_view(), name="leads"),
    path("demo-requests/", DemoRequestsView.as_view(), name="demo_requests"),
    path("demo-requests/<uuid:pk>/status/", DemoRequestUpdateView.as_view(), name="demo_request_update"),
    path("payments/", PaymentsView.as_view(), name="payments"),
    path("payments/<uuid:pk>/confirm/", ManualPaymentConfirmView.as_view(), name="payment_confirm"),
    path("support/", SupportView.as_view(), name="support"),
    path("support/<uuid:pk>/status/", SupportTicketUpdateView.as_view(), name="support_ticket_update"),
    path("documentation/", DocumentationView.as_view(), name="documentation"),
    path("marketing/", MarketingView.as_view(), name="marketing"),
    path("system-health/", SystemHealthView.as_view(), name="system_health"),
    path("activity/", ActivityLogsView.as_view(), name="activity"),
]
