from django.urls import path

from careers.views import CareersListView

app_name = "careers"

urlpatterns = [
    path("", CareersListView.as_view(), name="list"),
]
