from django.urls import path

from customer_portal.views import (
    DashboardView,
    DocumentationView,
    DownloadListView,
    InvoiceDetailView,
    InvoiceListView,
    LicenseListView,
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    ProductUpdateListView,
    ProfileView,
    SecuritySettingsView,
    SubscriptionListView,
    TicketCreateView,
    TicketDetailView,
    TicketListView,
)

app_name = "customer_portal"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("subscriptions/", SubscriptionListView.as_view(), name="subscriptions"),
    path("licenses/", LicenseListView.as_view(), name="licenses"),
    path("invoices/", InvoiceListView.as_view(), name="invoices"),
    path("invoices/<uuid:pk>/", InvoiceDetailView.as_view(), name="invoice_detail"),
    path("downloads/", DownloadListView.as_view(), name="downloads"),
    path("tickets/", TicketListView.as_view(), name="tickets"),
    path("tickets/new/", TicketCreateView.as_view(), name="ticket_create"),
    path("tickets/<uuid:pk>/", TicketDetailView.as_view(), name="ticket_detail"),
    path("updates/", ProductUpdateListView.as_view(), name="updates"),
    path("documentation/", DocumentationView.as_view(), name="documentation"),
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path("notifications/<uuid:pk>/read/", NotificationMarkReadView.as_view(), name="notification_read"),
    path("notifications/read-all/", NotificationMarkAllReadView.as_view(), name="notifications_read_all"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("security/", SecuritySettingsView.as_view(), name="security"),
]
