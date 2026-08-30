from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import AuditEventType, AuditLog
from payments.constants import MANUAL
from payments.models import GatewayConfiguration
from payments.services.checkout import create_checkout
from products.models import PricingPlan, Product

User = get_user_model()


class PaymentAuditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer@example.com",
            email="buyer@example.com",
            password="testpass123",
        )
        self.product = Product.objects.create(
            name="ChurchHub",
            slug="churchhub",
            is_published=True,
        )
        self.plan = PricingPlan.objects.create(
            product=self.product,
            name="Starter",
            slug="starter",
            is_published=True,
        )
        self.tier = self.plan.tiers.create(currency="GHS", region="global", amount=Decimal("49.00"))
        GatewayConfiguration.objects.create(code=MANUAL, name="Manual", is_active=True, is_default=True)

    def test_checkout_creates_payment_audit_event(self):
        create_checkout(
            user=self.user,
            amount=Decimal("49.00"),
            currency="GHS",
            gateway_code=MANUAL,
            pricing_plan=self.plan,
            pricing_tier=self.tier,
            manual_method="bank_transfer",
            manual_detail={"bank_name": "Test", "transfer_reference": "TRX-1"},
        )
        log = AuditLog.objects.get(event_type=AuditEventType.PAYMENT_CREATED)
        self.assertEqual(log.user, self.user)
        self.assertIn("PAY", log.metadata["reference"])
