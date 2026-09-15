"""
Audit and repair platform DB/UI consistency issues.

Usage:
    python manage.py sanitize_platform
    python manage.py sanitize_platform --fix
"""

from django.core.management.base import BaseCommand

from core.services.sanitize import run_sanitization


class Command(BaseCommand):
    help = (
        "Report (default) or repair (--fix) consistency issues across products, "
        "billing, and tenant-linked portal records."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help=(
                "Apply safe repairs: null organization backfill, license org alignment, "
                "featured-product policy, CoreTrust catalog fields, overdue trial expiry, "
                "status/date repairs, cross-user link detach, and Microfinance Core→CoreTrust copy."
            ),
        )

    def handle(self, *args, **options):
        fix = options["fix"]
        mode = "FIX" if fix else "DRY-RUN"
        self.stdout.write(self.style.NOTICE(f"sanitize_platform [{mode}]"))

        report = run_sanitization(fix=fix)
        errors = 0
        for finding in report.findings:
            style = self.style.SUCCESS
            if finding.severity == "warning":
                style = self.style.WARNING
            elif finding.severity == "error":
                style = self.style.ERROR
                if finding.count:
                    errors += 1
            line = f"[{finding.code}] {finding.message}"
            if finding.sample_ids:
                line += f" samples={finding.sample_ids}"
            self.stdout.write(style(line))

        self.stdout.write(
            self.style.NOTICE(
                f"Done. findings={len(report.findings)} fixed_total={report.fixed_total}"
            )
        )
        if errors and not fix:
            self.stdout.write(
                self.style.WARNING(
                    "Error-severity findings present. Re-run with --fix for safe repairs, "
                    "then investigate remaining report-only items."
                )
            )
