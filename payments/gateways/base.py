from abc import ABC, abstractmethod

from payments.gateways.dto import (
    GatewayResult,
    PaymentInitRequest,
    RecurringRequest,
    RefundRequest,
    WebhookResult,
)


class BasePaymentGateway(ABC):
    """Abstract payment gateway — all providers implement this interface."""

    code: str = ""
    display_name: str = ""
    supports_recurring: bool = False
    supports_refunds: bool = False
    supports_webhooks: bool = False

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @abstractmethod
    def initialize_payment(self, request: PaymentInitRequest) -> GatewayResult:
        """Start a one-time payment and return authorization details."""

    @abstractmethod
    def verify_payment(self, reference: str) -> GatewayResult:
        """Verify payment status with the provider."""

    def create_recurring(self, request: RecurringRequest) -> GatewayResult:
        raise NotImplementedError(f"{self.code} does not support recurring payments.")

    def cancel_recurring(self, gateway_subscription_id: str) -> GatewayResult:
        raise NotImplementedError(f"{self.code} does not support recurring cancellation.")

    def create_refund(self, request: RefundRequest) -> GatewayResult:
        raise NotImplementedError(f"{self.code} does not support refunds.")

    def verify_webhook(self, payload: bytes, headers: dict) -> bool:
        return True

    def parse_webhook(self, payload: dict, headers: dict) -> WebhookResult:
        return WebhookResult(handled=False, raw_payload=payload)

    def is_configured(self) -> bool:
        return bool(self.config.get("enabled"))
