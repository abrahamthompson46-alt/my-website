from django.contrib.auth.models import Permission
from django.db import models
from django.utils.text import slugify

from core.models import BaseModel


class Role(BaseModel):
    """Enterprise role with scoped Django permissions."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name="enterprise_roles")
    is_system = models.BooleanField(
        default=False,
        help_text="System roles cannot be deleted from the admin.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class UserRole(BaseModel):
    """Assigns a role to a user."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    assigned_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_roles",
    )

    class Meta:
        unique_together = [("user", "role")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} → {self.role.name}"
