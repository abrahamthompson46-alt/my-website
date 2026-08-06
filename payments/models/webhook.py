from django.db import models

from core.models import BaseModel


class WebhookEvent(BaseModel):
    gateway = models.ForeignKey(
        "payments.GatewayConfiguration",
        on_delete=models.CASCADE,
        related_name="webhook_events",
    )
    event_id = models.CharField(max_length=128)
    event_type = models.CharField(max_length=80, blank=True)
    payload = models.JSONField(default=dict)
    headers = models.JSONField(default=dict, blank=True)
    signature_valid = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    payment = models.ForeignKey(
        "payments.Payment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="webhook_events",
    )

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("gateway", "event_id")]
        indexes = [
            models.Index(fields=["processed", "created_at"]),
        ]

    def __str__(self):
        return f"{self.gateway.code} webhook {self.event_type or self.event_id}"
