from django.core.management.base import BaseCommand, CommandError

from ledger.calendar import run_end_of_day, run_end_of_day_for_all
from organizations.models import Organization


class Command(BaseCommand):
    help = "Run ledger end-of-day for one organization or all calendars."

    def add_arguments(self, parser):
        parser.add_argument(
            "--organization",
            dest="organization",
            help="Organization UUID or slug. Omit to process all calendars.",
        )
        parser.add_argument(
            "--notes",
            default="",
            help="Optional notes stored on the closed business day.",
        )

    def handle(self, *args, **options):
        notes = options.get("notes") or ""
        org_key = options.get("organization")
        if org_key:
            organization = (
                Organization.objects.filter(pk=org_key).first()
                or Organization.objects.filter(slug=org_key).first()
            )
            if organization is None:
                raise CommandError(f"Organization not found: {org_key}")
            day = run_end_of_day(organization, notes=notes)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Closed {day.business_date.isoformat()} for {organization.slug}"
                )
            )
            return

        results = run_end_of_day_for_all(notes=notes)
        closed = sum(1 for row in results if row.get("status") == "closed")
        errors = sum(1 for row in results if row.get("status") == "error")
        for row in results:
            if row.get("status") == "closed":
                self.stdout.write(
                    f"OK {row['organization']}: closed {row['closed_date']}"
                )
            else:
                self.stderr.write(
                    self.style.ERROR(
                        f"ERR {row['organization']}: {row.get('error', 'unknown')}"
                    )
                )
        self.stdout.write(self.style.SUCCESS(f"Done. closed={closed} errors={errors}"))
        if errors:
            raise CommandError(f"EOD completed with {errors} error(s).")
