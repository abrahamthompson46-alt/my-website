from decimal import Decimal
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase

from payments.gateways.dto import WebhookResult
from payments.models import GatewayConfiguration, Payment, PaymentStatus
from payments.services.webhooks import _validate_webhook_payment, process_webhook

User = get_user_model()


class WebhookValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="pay@test.com",
            email="pay@test.com",
            password="testpass123",
        )
        self.gateway = GatewayConfiguration.objects.create(
            code="paystack",
            name="Paystack",
            is_active=True,
            settings={"enabled": True, "secret_key": "sk_test"},
        )
        self.payment = Payment.objects.create(
            user=self.user,
            gateway=self.gateway,
            reference="PAY-TEST-001",
            gateway_reference="GW-123",
            amount=Decimal("99.00"),
            currency="GHS",
            status=PaymentStatus.PENDING,
            customer_email="pay@test.com",
        )

    def test_rejects_amount_mismatch(self):
        parsed = WebhookResult(
            handled=True,
            reference=self.payment.reference,
            gateway_reference="GW-123",
            status="succeeded",
            amount=Decimal("5000"),
            currency="GHS",
        )
        ok, reason = _validate_webhook_payment(self.payment, parsed, "paystack")
        self.assertFalse(ok)
        self.assertIn("Amount mismatch", reason)

    def test_accepts_matching_minor_units(self):
        parsed = WebhookResult(
            handled=True,
            reference=self.payment.reference,
            gateway_reference="GW-123",
            status="succeeded",
            amount=Decimal("9900"),
            currency="GHS",
        )
        ok, reason = _validate_webhook_payment(self.payment, parsed, "paystack")
        self.assertTrue(ok, reason)

    def test_rejects_already_succeeded(self):
        self.payment.status = PaymentStatus.SUCCEEDED
        self.payment.save()
        parsed = WebhookResult(
            handled=True,
            reference=self.payment.reference,
            status="succeeded",
            amount=Decimal("9900"),
            currency="GHS",
        )
        ok, reason = _validate_webhook_payment(self.payment, parsed, "paystack")
        self.assertFalse(ok)

    def test_process_webhook_records_mismatch_error(self):
        payload = {"event": "charge.success", "data": {"reference": self.payment.reference, "amount": 1, "currency": "GHS", "id": "evt_1"}}
        adapter = MagicMock()
        adapter.supports_webhooks = True
        adapter.verify_webhook.return_value = True
        adapter.parse_webhook.return_value = WebhookResult(
            handled=True,
            event_type="charge.success",
            reference=self.payment.reference,
            gateway_reference="GW-123",
            status="succeeded",
            amount=Decimal("1"),
            currency="GHS",
            raw_payload=payload,
        )

        from payments.services import webhooks as webhook_module

        original = webhook_module.get_gateway_from_model
        webhook_module.get_gateway_from_model = lambda _cfg: adapter
        try:
            event, _ = process_webhook(self.gateway, payload, b"{}", {})
        finally:
            webhook_module.get_gateway_from_model = original

        event.refresh_from_db()
        self.assertIn("Amount mismatch", event.error_message)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, PaymentStatus.PENDING)
