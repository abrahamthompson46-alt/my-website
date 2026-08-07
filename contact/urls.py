from django.urls import path

from contact.views import ContactView

app_name = "contact"

urlpatterns = [
    path("", ContactView.as_view(), name="form"),
    path("trial/", ContactView.as_view(), name="trial"),
    path("demo/", ContactView.as_view(), name="demo"),
]
