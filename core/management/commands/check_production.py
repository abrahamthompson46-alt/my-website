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

        if not getattr(settings, "SENTRY_DSN", None):
            warnings.append("SENTRY_DSN is not configured — error tracking is disabled.")

        backup_root = getattr(settings, "BACKUP_ROOT", "")
        if backup_root:
            warnings.append(
                f"Run `python manage.py check_backup_freshness` via cron to alert on stale backups ({backup_root})."
            )
        else:
            warnings.append("BACKUP_ROOT is not configured — backup freshness monitoring is disabled.")

        if "postgresql" in settings.DATABASES["default"]["ENGINE"]:
            db_options = settings.DATABASES["default"].get("OPTIONS") or {}
            if not db_options.get("sslmode"):
                warnings.append("DB OPTIONS.sslmode is unset — set DB_SSLMODE in production.")
            options_flags = db_options.get("options") or ""
            if "statement_timeout" not in options_flags:
                warnings.append(
                    "PostgreSQL statement_timeout is unset — set DB_STATEMENT_TIMEOUT_MS in production."
                )

        session_engine = getattr(settings, "SESSION_ENGINE", "")
        if session_engine.endswith(".cache") or "cached_db" in session_engine:
            if not settings.CACHES.get("default", {}).get("LOCATION"):
                issues.append("Cache-backed sessions require a configured Redis/cache LOCATION.")

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
