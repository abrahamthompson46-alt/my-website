"""
Seed enterprise RBAC roles.
Usage: python manage.py seed_roles
"""
from django.contrib.auth.models import Permission
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
            "add_productscreenshot",
            "change_productscreenshot",
            "view_productscreenshot",
            "delete_productscreenshot",
            "add_productvideo",
            "change_productvideo",
            "view_productvideo",
            "delete_productvideo",
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
        for role_data in DEFAULT_ROLES:
            perm_codenames = role_data.pop("permissions", [])
            role, created = Role.objects.get_or_create(
                slug=role_data["slug"],
                defaults=role_data,
            )
            if perm_codenames:
                perms = Permission.objects.filter(codename__in=perm_codenames)
                role.permissions.set(perms)
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action}: {role.name}")

        self.stdout.write(self.style.SUCCESS("Enterprise roles seeded."))
