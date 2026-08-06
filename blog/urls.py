from django.urls import path, re_path
from django.views.generic import RedirectView

app_name = "blog"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="marketing:blog_list", permanent=True), name="list"),
    path(
        "category/<slug:category_slug>/",
        RedirectView.as_view(pattern_name="marketing:blog_category", permanent=True),
        name="category",
    ),
    re_path(
        r"^(?P<slug>[-a-zA-Z0-9_.]+)/$",
        RedirectView.as_view(pattern_name="marketing:blog_detail", permanent=True),
        name="detail",
    ),
]
