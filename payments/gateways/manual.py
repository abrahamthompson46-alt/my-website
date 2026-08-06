from payments.constants import MANUAL
from payments.gateways.base import BasePaymentGateway
from payments.gateways.dto import GatewayResult, PaymentInitRequest, RefundRequest, WebhookResult


class ManualGateway(BasePaymentGateway):
    """
    Manual payment gateway for offline methods:
    bank transfer, cash, and cheque.
    """

    code = MANUAL
    display_name = "Manual Payment"
    supports_recurring = False
    supports_refunds = True
    supports_webhooks = False

    def is_configured(self) -> bool:
        return bool(self.config.get("enabled", True))

    def initialize_payment(self, request: PaymentInitRequest) -> GatewayResult:
        manual_method = request.metadata.get("manual_method", "bank_transfer")
        return GatewayResult(
            success=True,
            reference=request.reference,
            gateway_reference=request.reference,
            authorization_url="",
            status="pending_confirmation",
            message=f"Manual payment ({manual_method}) awaiting confirmation.",
            raw_response={"manual_method": manual_method},
        )

    def verify_payment(self, reference: str) -> GatewayResult:
        return GatewayResult(
            success=False,
            reference=reference,
            status="pending_confirmation",
            message="Manual payments require admin confirmation.",
        )

    def confirm_payment(self, reference: str, confirmed_by: str = "") -> GatewayResult:
        return GatewayResult(
            success=True,
            reference=reference,
            gateway_reference=reference,
            status="succeeded",
            message=f"Manual payment confirmed by {confirmed_by or 'admin'}.",
        )

    def create_refund(self, request: RefundRequest) -> GatewayResult:
        return GatewayResult(
            success=True,
            reference=request.payment_reference,
            gateway_reference=f"manual-refund-{request.payment_reference}",
            status="succeeded",
            message="Manual refund recorded.",
        )

    def parse_webhook(self, payload: dict, headers: dict) -> WebhookResult:
        return WebhookResult(handled=False, raw_payload=payload)
