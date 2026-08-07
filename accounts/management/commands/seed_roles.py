"""
Seed enterprise RBAC roles.
Usage: python manage.py seed_roles
"""
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Role


DEFAULT_ROLES = [
    {
        "name": "Customer",
        "slug": "customer",
        "description": "Standard customer portal access.",
        "is_system": True,
        "permissions": [],
    },
    {
        "name": "Support Agent",
        "slug": "support-agent",
        "description": "Support staff with ticket management access.",
        "is_system": True,
        "permissions": [],
    },
    {
        "name": "Billing Admin",
        "slug": "billing-admin",
        "description": "Manage subscriptions, invoices, and billing.",
        "is_system": True,
        "permissions": [],
    },
    {
        "name": "Platform Owner",
        "slug": "platform-owner",
        "description": "Full catalog, content, and platform administration.",
        "is_system": True,
        "permissions": [
            "add_product",
            "change_product",
            "view_product",
            "delete_product",
            "add_user",
            "change_user",
            "view_user",
        ],
    },
    {
        "name": "Platform Admin",
        "slug": "platform-admin",
        "description": "Full platform administration access.",
        "is_system": True,
        "permissions": ["add_user", "change_user", "view_user"],
    },
]


class Command(BaseCommand):
    help = "Seed enterprise RBAC roles."

    @transaction.atomic
    def handle(self, *args, **options):
        product_ct = ContentType.objects.get(app_label="products", model="product")
        user_ct = ContentType.objects.get(app_label="accounts", model="user")

        for role_data in DEFAULT_ROLES:
            perm_codenames = role_data.pop("permissions", [])
            role, created = Role.objects.get_or_create(
                slug=role_data["slug"],
                defaults=role_data,
            )
            if perm_codenames:
                perms = Permission.objects.filter(
                    codename__in=perm_codenames,
                    content_type__in=[product_ct, user_ct],
                )
                role.permissions.set(perms)
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action}: {role.name}")

        self.stdout.write(self.style.SUCCESS("Enterprise roles seeded."))
