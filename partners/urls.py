from django.urls import path

from partners.views import PartnerDashboardView

app_name = "partners"

urlpatterns = [
    path("", PartnerDashboardView.as_view(), name="dashboard"),
]
