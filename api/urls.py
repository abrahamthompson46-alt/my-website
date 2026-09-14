from django.urls import path

from api.views import (
    InvoiceDetailView,
    InvoiceListView,
    LicenseListView,
    MeView,
    ObtainAuthTokenView,
    OrganizationListView,
    SubscriptionListView,
    SupportTicketDetailView,
    SupportTicketListCreateView,
)

app_name = "api"

urlpatterns = [
    path("auth/token/", ObtainAuthTokenView.as_view(), name="auth_token"),
    path("me/", MeView.as_view(), name="me"),
    path("organizations/", OrganizationListView.as_view(), name="organizations"),
    path("subscriptions/", SubscriptionListView.as_view(), name="subscriptions"),
    path("invoices/", InvoiceListView.as_view(), name="invoices"),
    path("invoices/<uuid:pk>/", InvoiceDetailView.as_view(), name="invoice_detail"),
    path("licenses/", LicenseListView.as_view(), name="licenses"),
    path("tickets/", SupportTicketListCreateView.as_view(), name="tickets"),
    path("tickets/<uuid:pk>/", SupportTicketDetailView.as_view(), name="ticket_detail"),
]
