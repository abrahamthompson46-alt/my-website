import hashlib
import hmac

from django.conf import settings

from common.money import to_api_amount

from payments.constants import HUBTEL
from payments.gateways.base import BasePaymentGateway
from payments.gateways.dto import GatewayResult, PaymentInitRequest, RefundRequest, WebhookResult
from payments.gateways.http import HTTPGatewayMixin


class HubtelGateway(HTTPGatewayMixin, BasePaymentGateway):
    code = HUBTEL
    display_name = "Hubtel"
    supports_recurring = True
    supports_refunds = True
    supports_webhooks = True
    api_base_url = "https://api.hubtel.com/v2"

    def is_configured(self) -> bool:
        return bool(
            self.config.get("enabled")
            and self.config.get("client_id")
            and self.config.get("client_secret")
        )

    def _auth_headers(self):
        import base64

        creds = f"{self.config['client_id']}:{self.config['client_secret']}"
        token = base64.b64encode(creds.encode("utf-8")).decode("utf-8")
        return {"Authorization": f"Basic {token}"}

    def initialize_payment(self, request: PaymentInitRequest) -> GatewayResult:
        payload = {
            "totalAmount": to_api_amount(request.amount),
            "description": request.metadata.get("description", "Payment"),
            "callbackUrl": request.callback_url,
            "returnUrl": request.callback_url,
            "cancellationUrl": request.metadata.get("cancel_url", request.callback_url),
            "clientReference": request.reference,
            "payeeName": request.metadata.get("customer_name", request.email),
            "payeeMobileNumber": request.metadata.get("phone", ""),
            "payeeEmail": request.email,
        }
        merchant = self.config.get("merchant_account_number", "")
        response = self._request(
            "POST",
            f"/pos/onlinecheckout/items/initiate/{merchant}",
            payload,
            self._auth_headers(),
        )
        data = response.get("data", response)
        return GatewayResult(
            success=response.get("responseCode") == "0000" or bool(data.get("checkoutUrl")),
            reference=request.reference,
            gateway_reference=data.get("checkoutId", request.reference),
            authorization_url=data.get("checkoutUrl", ""),
            status="pending",
            message=response.get("message", ""),
            raw_response=response,
        )

    def verify_payment(self, reference: str) -> GatewayResult:
        response = self._request(
            "GET",
            f"/pos/onlinecheckout/items/status/{reference}",
            headers=self._auth_headers(),
        )
        data = response.get("data", response)
        status = "succeeded" if data.get("status") == "Paid" else data.get("status", "pending").lower()
        return GatewayResult(
            success=status == "succeeded",
            reference=reference,
            gateway_reference=data.get("checkoutId", reference),
            status=status,
            message=response.get("message", ""),
            raw_response=response,
        )

    def create_refund(self, request: RefundRequest) -> GatewayResult:
        payload = {
            "clientReference": request.payment_reference,
            "amount": to_api_amount(request.amount),
            "reason": request.reason,
        }
        response = self._request("POST", "/refund/initiate", payload, self._auth_headers())
        return GatewayResult(
            success=response.get("responseCode") == "0000",
            reference=request.payment_reference,
            gateway_reference=response.get("data", {}).get("refundId", ""),
            status="pending",
            message=response.get("message", ""),
            raw_response=response,
        )

    def verify_webhook(self, payload: bytes, headers: dict) -> bool:
        secret = self.config.get("webhook_secret") or getattr(settings, "HUBTEL_WEBHOOK_SECRET", "")
        if not secret:
            return False
        signature = headers.get("X-Hubtel-Signature") or headers.get("x-hubtel-signature", "")
        digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature)

    def parse_webhook(self, payload: dict, headers: dict) -> WebhookResult:
        status = payload.get("Status", payload.get("status", "")).lower()
        status_map = {"paid": "succeeded", "failed": "failed", "refunded": "refunded"}
        return WebhookResult(
            handled=True,
            event_type=payload.get("EventType", "payment.update"),
            reference=payload.get("ClientReference", payload.get("clientReference", "")),
            gateway_reference=payload.get("CheckoutId", payload.get("checkoutId", "")),
            status=status_map.get(status, status),
            amount=payload.get("Amount"),
            currency=payload.get("Currency", "GHS"),
            message=payload.get("Message", ""),
            raw_payload=payload,
        )
