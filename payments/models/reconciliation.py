from django.db import models

from core.models import BaseModel


class ReconciliationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    MATCHED = "matched", "Matched"
    DISCREPANCY = "discrepancy", "Discrepancy"
    RESOLVED = "resolved", "Resolved"


class ReconciliationRun(BaseModel):
    """Batch reconciliation between gateway and internal records."""

    gateway = models.ForeignKey(
        "payments.GatewayConfiguration",
        on_delete=models.CASCADE,
        related_name="reconciliation_runs",
    )
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=ReconciliationStatus.choices,
        default=ReconciliationStatus.PENDING,
    )
    gateway_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    internal_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discrepancy_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    matched_count = models.PositiveIntegerField(default=0)
    unmatched_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    run_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reconciliation_runs",
    )

    class Meta:
        ordering = ["-period_end", "-created_at"]

    def __str__(self):
        return f"{self.gateway.code} reconciliation {self.period_start}–{self.period_end}"


class ReconciliationEntry(BaseModel):
    """Line item in a reconciliation run."""

    run = models.ForeignKey(
        ReconciliationRun,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    payment = models.ForeignKey(
        "payments.Payment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reconciliation_entries",
    )
    gateway_reference = models.CharField(max_length=128, blank=True)
    internal_reference = models.CharField(max_length=64, blank=True)
    gateway_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    internal_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_matched = models.BooleanField(default=False)
    discrepancy = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Entry {self.internal_reference or self.gateway_reference}"
