import hashlib
import hmac

from django.conf import settings

from common.money import to_api_amount, to_minor_units

from payments.constants import PAYSTACK
from payments.gateways.base import BasePaymentGateway
from payments.gateways.dto import (
    GatewayResult,
    PaymentInitRequest,
    RecurringRequest,
    RefundRequest,
    WebhookResult,
)
from payments.gateways.http import HTTPGatewayMixin


class PaystackGateway(HTTPGatewayMixin, BasePaymentGateway):
    code = PAYSTACK
    display_name = "Paystack"
    supports_recurring = True
    supports_refunds = True
    supports_webhooks = True
    api_base_url = "https://api.paystack.co"

    def is_configured(self) -> bool:
        return bool(self.config.get("enabled") and self.config.get("secret_key"))

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.config['secret_key']}"}

    def initialize_payment(self, request: PaymentInitRequest) -> GatewayResult:
        amount_kobo = to_minor_units(request.amount)
        payload = {
            "email": request.email,
            "amount": amount_kobo,
            "currency": request.currency,
            "reference": request.reference,
            "callback_url": request.callback_url,
            "metadata": request.metadata,
        }
        response = self._request("POST", "/transaction/initialize", payload, self._auth_headers())
        data = response.get("data", {})
        return GatewayResult(
            success=response.get("status", False),
            reference=request.reference,
            gateway_reference=data.get("reference", request.reference),
            authorization_url=data.get("authorization_url", ""),
            status="pending",
            message=response.get("message", ""),
            raw_response=response,
        )

    def verify_payment(self, reference: str) -> GatewayResult:
        response = self._request("GET", f"/transaction/verify/{reference}", headers=self._auth_headers())
        data = response.get("data", {})
        status = "succeeded" if data.get("status") == "success" else data.get("status", "failed")
        return GatewayResult(
            success=data.get("status") == "success",
            reference=reference,
            gateway_reference=data.get("reference", reference),
            status=status,
            message=response.get("message", ""),
            raw_response=response,
        )

    def create_recurring(self, request: RecurringRequest) -> GatewayResult:
        amount_kobo = to_minor_units(request.amount)
        payload = {
            "name": request.metadata.get("plan_name", "Subscription"),
            "interval": request.interval,
            "amount": amount_kobo,
            "currency": request.currency,
        }
        response = self._request("POST", "/plan", payload, self._auth_headers())
        data = response.get("data", {})
        return GatewayResult(
            success=response.get("status", False),
            reference=request.reference,
            gateway_reference=str(data.get("plan_code", "")),
            status="active" if response.get("status") else "failed",
            message=response.get("message", ""),
            raw_response=response,
        )

    def create_refund(self, request: RefundRequest) -> GatewayResult:
        payload = {
            "transaction": request.gateway_reference,
            "amount": to_minor_units(request.amount),
            "currency": request.currency,
            "customer_note": request.reason,
        }
        response = self._request("POST", "/refund", payload, self._auth_headers())
        data = response.get("data", {})
        return GatewayResult(
            success=response.get("status", False),
            reference=request.payment_reference,
            gateway_reference=str(data.get("id", "")),
            status=data.get("status", "pending"),
            message=response.get("message", ""),
            raw_response=response,
        )

    def verify_webhook(self, payload: bytes, headers: dict) -> bool:
        secret = self.config.get("webhook_secret") or getattr(settings, "PAYSTACK_WEBHOOK_SECRET", "")
        if not secret:
            return False
        signature = headers.get("X-Paystack-Signature") or headers.get("x-paystack-signature", "")
        digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha512).hexdigest()
        return hmac.compare_digest(digest, signature)

    def parse_webhook(self, payload: dict, headers: dict) -> WebhookResult:
        event = payload.get("event", "")
        data = payload.get("data", {})
        status_map = {
            "charge.success": "succeeded",
            "subscription.create": "active",
            "refund.processed": "refunded",
        }
        return WebhookResult(
            handled=True,
            event_type=event,
            reference=data.get("reference", ""),
            gateway_reference=str(data.get("id", data.get("reference", ""))),
            status=status_map.get(event, data.get("status", "")),
            amount=data.get("amount"),
            currency=data.get("currency", ""),
            message=event,
            raw_payload=payload,
        )
