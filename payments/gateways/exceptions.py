class PaymentGatewayError(Exception):
    """Base payment gateway error."""


class GatewayNotConfiguredError(PaymentGatewayError):
    """Gateway credentials or configuration missing."""


class GatewayAPIError(PaymentGatewayError):
    """Provider API returned an error."""

    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class WebhookVerificationError(PaymentGatewayError):
    """Webhook signature verification failed."""
