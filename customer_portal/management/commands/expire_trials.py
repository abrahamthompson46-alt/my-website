"""Expire trials past their end date and notify customers."""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Expire overdue trials and send 3-day expiry reminders."

    def handle(self, *args, **options):
        from common.services.onboarding_email import send_trial_expiring_email
        from common.services.trial_provisioning import expire_due_trials
        from customer_portal.models import Subscription
        from customer_portal.models.subscription import SubscriptionStatus

        expired = expire_due_trials()
        self.stdout.write(self.style.SUCCESS(f"Expired {expired} trial(s)."))

        today = timezone.now().date()
        reminder_date = today + timedelta(days=3)
        reminders = 0
        from customer_portal.models import Subscription

        for sub in Subscription.objects.filter(
            status=SubscriptionStatus.TRIAL,
            trial_ends_at=reminder_date,
        ).select_related("user", "product"):
            try:
                send_trial_expiring_email(sub.user, sub, days_left=3)
                reminders += 1
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"Reminder failed for {sub.user.email}: {exc}"))
        self.stdout.write(self.style.SUCCESS(f"Sent {reminders} trial reminder(s)."))
