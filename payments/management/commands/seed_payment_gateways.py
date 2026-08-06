"""
Seed payment gateway configurations.
Usage: python manage.py seed_payment_gateways
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from payments.constants import FLUTTERWAVE, HUBTEL, MANUAL, PAYSTACK
from payments.models import GatewayConfiguration


GATEWAYS = [
    {
        "code": PAYSTACK,
        "name": "Paystack",
        "is_default": True,
        "supports_recurring": True,
        "supports_refunds": True,
        "settings": {"public_key_env": "PAYSTACK_PUBLIC_KEY"},
    },
    {
        "code": HUBTEL,
        "name": "Hubtel",
        "supports_recurring": True,
        "supports_refunds": True,
        "settings": {"merchant_account_env": "HUBTEL_MERCHANT_ACCOUNT"},
    },
    {
        "code": FLUTTERWAVE,
        "name": "Flutterwave",
        "supports_recurring": True,
        "supports_refunds": True,
        "settings": {"public_key_env": "FLUTTERWAVE_PUBLIC_KEY"},
    },
    {
        "code": MANUAL,
        "name": "Manual Payments",
        "is_active": True,
        "supports_recurring": False,
        "supports_refunds": True,
        "settings": {"allowed_methods": ["bank_transfer", "cash", "cheque"]},
    },
]


class Command(BaseCommand):
    help = "Seed payment gateway configurations."

    @transaction.atomic
    def handle(self, *args, **options):
        for data in GATEWAYS:
            gateway, created = GatewayConfiguration.objects.update_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "is_active": data.get("is_active", False),
                    "is_default": data.get("is_default", False),
                    "supports_recurring": data.get("supports_recurring", False),
                    "supports_refunds": data.get("supports_refunds", True),
                    "settings": data.get("settings", {}),
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action}: {gateway.name}")

        manual = GatewayConfiguration.objects.get(code=MANUAL)
        manual.is_active = True
        manual.save(update_fields=["is_active", "updated_at"])
        self.stdout.write(self.style.SUCCESS("Payment gateways seeded. Manual payments enabled by default."))
