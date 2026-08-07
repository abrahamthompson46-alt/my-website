"""
Production readiness checks.
Usage: python manage.py check_production
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Verify production configuration before go-live."

    def handle(self, *args, **options):
        issues = []
        warnings = []

        if settings.DEBUG:
            issues.append("DEBUG is True — must be False in production.")

        if "sqlite" in settings.DATABASES["default"]["ENGINE"]:
            issues.append("SQLite database — use PostgreSQL in production.")

        secret = getattr(settings, "SECRET_KEY", "")
        if len(secret) < 50:
            issues.append("SECRET_KEY is too short (need 50+ characters).")

        if settings.EMAIL_BACKEND.endswith("console.EmailBackend"):
            issues.append("Console email backend — configure SMTP or file backend.")

        redis_url = getattr(settings, "REDIS_URL", None) or settings.CACHES.get("default", {}).get("LOCATION")
        if not redis_url and not getattr(settings, "CACHES", {}).get("default", {}).get("LOCATION"):
            warnings.append("Redis/cache not configured — sessions may not persist across workers.")

        if not getattr(settings, "CSRF_TRUSTED_ORIGINS", []):
            issues.append("CSRF_TRUSTED_ORIGINS is empty.")

        if not getattr(settings, "ALLOWED_HOSTS", []) or set(settings.ALLOWED_HOSTS) <= {"localhost", "127.0.0.1"}:
            issues.append("ALLOWED_HOSTS must include your production domain(s).")

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as exc:
            issues.append(f"Database connection failed: {exc}")

        static_backend = settings.STORAGES.get("staticfiles", {}).get("BACKEND", "")
        if "Manifest" in static_backend:
            warnings.append(
                "Manifest static storage is enabled — run collectstatic with production settings "
                "and verify staticfiles/staticfiles.json exists."
            )

        if issues:
            self.stdout.write(self.style.ERROR("BLOCKERS:"))
            for item in issues:
                self.stdout.write(f"  ✗ {item}")

        if warnings:
            self.stdout.write(self.style.WARNING("WARNINGS:"))
            for item in warnings:
                self.stdout.write(f"  ! {item}")

        if not issues and not warnings:
            self.stdout.write(self.style.SUCCESS("All production checks passed."))
        elif not issues:
            self.stdout.write(self.style.SUCCESS("No blockers — review warnings before go-live."))
        else:
            self.stdout.write(self.style.ERROR("Fix blockers before deploying to production."))
