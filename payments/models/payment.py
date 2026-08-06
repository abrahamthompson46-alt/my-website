from django.db import models
from django.db.models import Sum
from django.utils.text import slugify

from common.money import ZERO, quantize_money
from core.models import BaseModel


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    PENDING_CONFIRMATION = "pending_confirmation", "Pending Confirmation"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"
    PARTIALLY_REFUNDED = "partially_refunded", "Partially Refunded"


class PaymentType(models.TextChoices):
    ONE_TIME = "one_time", "One-time"
    RECURRING = "recurring", "Recurring"
    MANUAL = "manual", "Manual"


class ManualPaymentMethod(models.TextChoices):
    BANK_TRANSFER = "bank_transfer", "Bank Transfer"
    CASH = "cash", "Cash"
    CHEQUE = "cheque", "Cheque"


class Payment(BaseModel):
    """Core payment record — gateway-agnostic."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    gateway = models.ForeignKey(
        "payments.GatewayConfiguration",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    reference = models.CharField(max_length=64, unique=True)
    gateway_reference = models.CharField(max_length=128, blank=True)
    idempotency_key = models.CharField(max_length=128, unique=True, blank=True)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.ONE_TIME,
    )
    manual_method = models.CharField(
        max_length=20,
        choices=ManualPaymentMethod.choices,
        blank=True,
    )

    description = models.CharField(max_length=255, blank=True)
    customer_email = models.EmailField(blank=True)
    authorization_url = models.URLField(blank=True)
    callback_url = models.URLField(blank=True)

    invoice = models.ForeignKey(
        "customer_portal.Invoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    pricing_plan = models.ForeignKey(
        "products.PricingPlan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    pricing_tier = models.ForeignKey(
        "products.PricingTier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )

    metadata = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["gateway_reference"]),
        ]

    def __str__(self):
        return f"{self.reference} ({self.amount} {self.currency})"

    @property
    def is_manual(self):
        return bool(self.manual_method)

    @property
    def refundable_amount(self):
        refunded = self.refunds.filter(
            status__in=["succeeded", "pending"]
        ).aggregate(total=Sum("amount"))["total"] or ZERO
        return max(quantize_money(self.amount - refunded), ZERO)


class PaymentAttempt(BaseModel):
    """Individual charge or verification attempt."""

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="attempts")
    gateway_reference = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=30, choices=PaymentStatus.choices)
    response_data = models.JSONField(default=dict, blank=True)
    error_message = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.payment.reference} attempt ({self.status})"


class ManualPaymentDetail(BaseModel):
    """Extra details for manual/offline payments."""

    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="manual_detail")
    bank_name = models.CharField(max_length=120, blank=True)
    account_number = models.CharField(max_length=64, blank=True)
    transfer_reference = models.CharField(max_length=128, blank=True)
    cheque_number = models.CharField(max_length=64, blank=True)
    receipt_number = models.CharField(max_length=64, blank=True)
    received_by = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    proof_document = models.FileField(upload_to="payments/proofs/", blank=True)
    confirmed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_manual_payments",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Manual detail for {self.payment.reference}"
