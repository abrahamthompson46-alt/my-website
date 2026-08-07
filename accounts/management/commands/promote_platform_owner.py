"""
Promote a user to platform owner with staff access and the platform-owner role.

Usage:
    python manage.py seed_roles
    python manage.py promote_platform_owner abrahamthompson46@gmail.com
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import transaction

from accounts.models import Role
from accounts.services.email import get_or_create_security_profile
from accounts.services.rbac import assign_role

User = get_user_model()


class Command(BaseCommand):
    help = "Grant staff access and assign the platform-owner role to a user."

    def add_arguments(self, parser):
        parser.add_argument("email", help="Email address of the user to promote")

    @transaction.atomic
    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        call_command("seed_roles")

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise CommandError(f"No user found with email: {email}")

        role = Role.objects.filter(slug="platform-owner").first()
        if not role:
            raise CommandError("platform-owner role missing — run: python manage.py seed_roles")

        updated_fields = []
        if not user.is_staff:
            user.is_staff = True
            updated_fields.append("is_staff")
        if not user.is_superuser:
            user.is_superuser = True
            updated_fields.append("is_superuser")
        if not user.is_active:
            user.is_active = True
            updated_fields.append("is_active")
        if updated_fields:
            user.save(update_fields=updated_fields)

        profile = get_or_create_security_profile(user)
        if not profile.email_verified:
            profile.email_verified = True
            profile.save(update_fields=["email_verified", "updated_at"])

        user_role, created = assign_role(user, role)
        action = "Assigned" if created else "Already has"
        self.stdout.write(self.style.SUCCESS(
            f"{action} platform-owner role for {user.email} (staff={user.is_staff}, superuser={user.is_superuser})"
        ))
        self.stdout.write("Next: log in at /accounts/login/, enroll MFA, then open /control/")
