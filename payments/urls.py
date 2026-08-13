from django.urls import path

from payments.models import ManualPaymentMethod
from payments.views import (
    CheckoutView,
    PaymentDetailView,
    PaymentListView,
    PaymentProofDownloadView,
    PaymentReturnView,
)

app_name = "payments"

urlpatterns = [
    path("", PaymentListView.as_view(), name="list"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("return/<str:reference>/", PaymentReturnView.as_view(), name="return"),
    path("<uuid:pk>/proof/", PaymentProofDownloadView.as_view(), name="proof_download"),
    path("<uuid:pk>/", PaymentDetailView.as_view(), name="detail"),
]
