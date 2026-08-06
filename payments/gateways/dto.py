from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class GatewayResult:
    success: bool
    reference: str = ""
    gateway_reference: str = ""
    authorization_url: str = ""
    status: str = ""
    message: str = ""
    raw_response: dict = field(default_factory=dict)


@dataclass
class WebhookResult:
    handled: bool
    event_type: str = ""
    reference: str = ""
    gateway_reference: str = ""
    status: str = ""
    amount: Decimal | None = None
    currency: str = ""
    message: str = ""
    raw_payload: dict = field(default_factory=dict)


@dataclass
class PaymentInitRequest:
    reference: str
    amount: Decimal
    currency: str
    email: str
    callback_url: str
    metadata: dict = field(default_factory=dict)
    idempotency_key: str = ""


@dataclass
class RefundRequest:
    payment_reference: str
    gateway_reference: str
    amount: Decimal
    currency: str
    reason: str = ""


@dataclass
class RecurringRequest:
    reference: str
    amount: Decimal
    currency: str
    email: str
    interval: str
    callback_url: str
    metadata: dict = field(default_factory=dict)
