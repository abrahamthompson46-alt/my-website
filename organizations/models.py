from django.db import models
from django.utils.text import slugify

from core.models import BaseModel


class OrganizationStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    ARCHIVED = "archived", "Archived"


class Organization(BaseModel):
    """Tenant workspace shared by members (shared-schema multi-tenancy)."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    status = models.CharField(
        max_length=20,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.ACTIVE,
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_organizations",
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["status", "slug"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:180] or "org"
            candidate = base
            n = 1
            while Organization.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                n += 1
                candidate = f"{base}-{n}"
            self.slug = candidate
        super().save(*args, **kwargs)


class MembershipRole(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    BILLING = "billing", "Billing"


class MembershipStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INVITED = "invited", "Invited"
    SUSPENDED = "suspended", "Suspended"
    LEFT = "left", "Left"


class OrganizationMembership(BaseModel):
    """Links a user to an organization with a tenant-scoped role."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=MembershipRole.choices,
        default=MembershipRole.MEMBER,
    )
    status = models.CharField(
        max_length=20,
        choices=MembershipStatus.choices,
        default=MembershipStatus.ACTIVE,
    )
    invited_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organization_invites_sent",
    )
    joined_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["organization__name", "user__email"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                name="uniq_organization_membership_user",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["organization", "status", "role"]),
        ]

    def __str__(self):
        return f"{self.user} @ {self.organization} ({self.role})"
