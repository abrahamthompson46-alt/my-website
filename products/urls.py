from django.urls import path

from products.views import (
    PlanStartView,
    ProductCompareView,
    ProductDetailView,
    ProductListView,
    ProductPricingView,
)

app_name = "products"

urlpatterns = [
    path("", ProductListView.as_view(), name="list"),
    path("compare/", ProductCompareView.as_view(), name="compare"),
    path("category/<slug:category_slug>/", ProductListView.as_view(), name="category"),
    path("<slug:slug>/", ProductDetailView.as_view(), name="detail"),
    path("<slug:slug>/pricing/", ProductPricingView.as_view(), name="pricing"),
    path("<slug:slug>/start/", PlanStartView.as_view(), name="plan_start"),
]
