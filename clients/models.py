"""Organization-scoped MFI borrower / client registry."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import BaseModel


class ClientType(models.TextChoices):
    INDIVIDUAL = "individual", "Individual"
    GROUP = "group", "Group"
    BUSINESS = "business", "Business"


class ClientStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    BLACKLISTED = "blacklisted", "Blacklisted"
    CLOSED = "closed", "Closed"


class Client(BaseModel):
    """
    Microfinance borrower / client record scoped to one organization.

    Distinct from platform ``customer_portal`` accounts (Zreta SaaS billing).
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="mfi_clients",
    )
    client_number = models.CharField(max_length=32)
    client_type = models.CharField(
        max_length=20,
        choices=ClientType.choices,
        default=ClientType.INDIVIDUAL,
    )
    status = models.CharField(
        max_length=20,
        choices=ClientStatus.choices,
        default=ClientStatus.ACTIVE,
    )
    display_name = models.CharField(max_length=200)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    other_names = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    national_id = models.CharField(max_length=64, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, default="GH")
    notes = models.TextField(blank=True)
    external_reference = models.CharField(max_length=64, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_mfi_clients",
    )

    class Meta:
        ordering = ["organization", "client_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "client_number"],
                name="uniq_mfi_client_org_number",
            ),
            models.UniqueConstraint(
                fields=["organization", "national_id"],
                condition=~models.Q(national_id=""),
                name="uniq_mfi_client_org_national_id",
            ),
        ]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "client_type"]),
            models.Index(fields=["organization", "phone"]),
            models.Index(fields=["organization", "display_name"]),
        ]

    def __str__(self):
        return f"{self.client_number} — {self.display_name}"

    def clean(self):
        super().clean()
        if self.client_type == ClientType.INDIVIDUAL:
            if not (self.first_name or self.last_name or self.display_name):
                raise ValidationError(
                    "Individual clients require a name (first/last or display name)."
                )

    def save(self, *args, **kwargs):
        if not self.display_name:
            parts = [self.first_name, self.other_names, self.last_name]
            assembled = " ".join(p.strip() for p in parts if p and p.strip())
            self.display_name = assembled or self.client_number
        if self.national_id:
            self.national_id = self.national_id.strip()
        if self.client_number:
            self.client_number = self.client_number.strip().upper()
        if self.country:
            self.country = self.country.strip().upper()[:2] or "GH"
        super().save(*args, **kwargs)
