from django.urls import path

from support.views import SupportIndexView

app_name = "support"

urlpatterns = [
    path("", SupportIndexView.as_view(), name="index"),
]
