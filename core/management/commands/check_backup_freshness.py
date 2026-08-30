"""
Verify backup freshness for monitoring and cron alerts.
Usage: python manage.py check_backup_freshness
"""
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Fail if the latest database backup is older than the allowed age."

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-age-hours",
            type=int,
            default=getattr(settings, "BACKUP_MAX_AGE_HOURS", 26),
            help="Maximum allowed backup age in hours (default: 26).",
        )

    def handle(self, *args, **options):
        backup_root = Path(getattr(settings, "BACKUP_ROOT", "/var/backups/zreta"))
        database_dir = backup_root / "database"
        max_age_hours = options["max_age_hours"]

        if not database_dir.is_dir():
            self.stdout.write(self.style.ERROR(f"Backup directory not found: {database_dir}"))
            raise SystemExit(1)

        backups = [path for path in database_dir.iterdir() if path.is_dir()]
        if not backups:
            self.stdout.write(self.style.ERROR(f"No database backups found in {database_dir}"))
            raise SystemExit(1)

        latest = max(backups, key=lambda path: path.stat().st_mtime)
        age_hours = (datetime.now(timezone.utc).timestamp() - latest.stat().st_mtime) / 3600

        if age_hours > max_age_hours:
            self.stdout.write(
                self.style.ERROR(
                    f"Latest backup {latest.name} is {age_hours:.1f}h old "
                    f"(limit {max_age_hours}h)."
                )
            )
            raise SystemExit(1)

        self.stdout.write(
            self.style.SUCCESS(
                f"Latest backup {latest.name} is {age_hours:.1f}h old (within {max_age_hours}h limit)."
            )
        )
