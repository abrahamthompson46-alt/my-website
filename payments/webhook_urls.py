from django.urls import path

from payments.views import GatewayWebhookView

app_name = "payments_webhooks"

urlpatterns = [
    path("<str:gateway_code>/", GatewayWebhookView.as_view(), name="webhook"),
]
