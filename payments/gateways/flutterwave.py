import hashlib
import hmac

from django.conf import settings

from common.money import to_api_amount

from payments.constants import FLUTTERWAVE
from payments.gateways.base import BasePaymentGateway
from payments.gateways.dto import (
    GatewayResult,
    PaymentInitRequest,
    RecurringRequest,
    RefundRequest,
    WebhookResult,
)
from payments.gateways.http import HTTPGatewayMixin


class FlutterwaveGateway(HTTPGatewayMixin, BasePaymentGateway):
    code = FLUTTERWAVE
    display_name = "Flutterwave"
    supports_recurring = True
    supports_refunds = True
    supports_webhooks = True
    api_base_url = "https://api.flutterwave.com/v3"

    def is_configured(self) -> bool:
        return bool(self.config.get("enabled") and self.config.get("secret_key"))

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.config['secret_key']}"}

    def initialize_payment(self, request: PaymentInitRequest) -> GatewayResult:
        payload = {
            "tx_ref": request.reference,
            "amount": to_api_amount(request.amount),
            "currency": request.currency,
            "redirect_url": request.callback_url,
            "customer": {
                "email": request.email,
                "name": request.metadata.get("customer_name", request.email),
            },
            "meta": request.metadata,
        }
        response = self._request("POST", "/payments", payload, self._auth_headers())
        data = response.get("data", {})
        return GatewayResult(
            success=response.get("status") == "success",
            reference=request.reference,
            gateway_reference=str(data.get("id", request.reference)),
            authorization_url=data.get("link", ""),
            status="pending",
            message=response.get("message", ""),
            raw_response=response,
        )

    def verify_payment(self, reference: str) -> GatewayResult:
        response = self._request(
            "GET",
            f"/transactions/verify_by_reference?tx_ref={reference}",
            headers=self._auth_headers(),
        )
        data = response.get("data", {})
        status = "succeeded" if data.get("status") == "successful" else data.get("status", "failed")
        return GatewayResult(
            success=data.get("status") == "successful",
            reference=reference,
            gateway_reference=str(data.get("id", reference)),
            status=status,
            message=response.get("message", ""),
            raw_response=response,
        )

    def create_recurring(self, request: RecurringRequest) -> GatewayResult:
        payload = {
            "amount": to_api_amount(request.amount),
            "currency": request.currency,
            "interval": request.interval,
            "name": request.metadata.get("plan_name", "Subscription"),
        }
        response = self._request("POST", "/payment-plans", payload, self._auth_headers())
        data = response.get("data", {})
        return GatewayResult(
            success=response.get("status") == "success",
            reference=request.reference,
            gateway_reference=str(data.get("id", "")),
            status="active" if response.get("status") == "success" else "failed",
            message=response.get("message", ""),
            raw_response=response,
        )

    def create_refund(self, request: RefundRequest) -> GatewayResult:
        payload = {
            "amount": to_api_amount(request.amount),
            "comments": request.reason,
        }
        response = self._request(
            "POST",
            f"/transactions/{request.gateway_reference}/refund",
            payload,
            self._auth_headers(),
        )
        data = response.get("data", {})
        return GatewayResult(
            success=response.get("status") == "success",
            reference=request.payment_reference,
            gateway_reference=str(data.get("id", "")),
            status="pending",
            message=response.get("message", ""),
            raw_response=response,
        )

    def verify_webhook(self, payload: bytes, headers: dict) -> bool:
        secret = self.config.get("webhook_secret") or getattr(settings, "FLUTTERWAVE_WEBHOOK_SECRET", "")
        if not secret:
            return False
        signature = headers.get("verif-hash") or headers.get("Verif-Hash", "")
        return hmac.compare_digest(signature, secret)

    def parse_webhook(self, payload: dict, headers: dict) -> WebhookResult:
        event = payload.get("event", payload.get("event.type", ""))
        data = payload.get("data", payload)
        status_map = {
            "charge.completed": "succeeded",
            "subscription.cancelled": "cancelled",
            "refund.completed": "refunded",
        }
        return WebhookResult(
            handled=True,
            event_type=event,
            reference=data.get("tx_ref", data.get("txRef", "")),
            gateway_reference=str(data.get("id", "")),
            status=status_map.get(event, data.get("status", "")),
            amount=data.get("amount"),
            currency=data.get("currency", ""),
            message=event,
            raw_payload=payload,
        )
