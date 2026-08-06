"""
Ensure security profiles exist for all users.
Usage: python manage.py ensure_security_profiles
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import UserSecurityProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Create security profiles for users missing them."

    def handle(self, *args, **options):
        created = 0
        for user in User.objects.all():
            _, was_created = UserSecurityProfile.objects.get_or_create(user=user)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Security profiles ensured. Created {created} new profiles."))
