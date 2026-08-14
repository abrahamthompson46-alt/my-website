from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.services.email import get_or_create_security_profile
from customer_portal.models import Invoice
from customer_portal.models.invoice import InvoiceStatus
from payments.constants import MANUAL
from payments.models import GatewayConfiguration, ManualPaymentDetail, Payment, PaymentStatus
from payments.services.pricing import CheckoutPricingError, resolve_checkout_pricing
from products.models import PricingPlan, Product, ProductCategory, ProductStatus

User = get_user_model()


class CheckoutPricingServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer@example.com",
            email="buyer@example.com",
            password="SecurePass123!",
        )
        self.other = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="SecurePass123!",
        )
        category = ProductCategory.objects.create(name="Vertical", slug="vertical")
        self.product = Product.objects.create(
            name="ChurchHub",
            slug="churchhub",
            category=category,
            is_published=True,
            status=ProductStatus.GA,
        )
        self.plan = PricingPlan.objects.create(
            product=self.product,
            name="Starter",
            slug="starter",
            is_published=True,
        )
        self.tier = self.plan.tiers.create(currency="GHS", region="global", amount=Decimal("49.00"))
        self.invoice = Invoice.objects.create(
            user=self.user,
            invoice_number="INV-1001",
            amount=Decimal("99.00"),
            currency="GHS",
            status=InvoiceStatus.OPEN,
            issued_at="2026-01-01",
            due_at="2026-01-31",
        )
        GatewayConfiguration.objects.create(code=MANUAL, name="Manual", is_active=True, is_default=True)

    def _pricing(self, **kwargs):
        return resolve_checkout_pricing(user=self.user, **kwargs)

    def test_plan_checkout_resolves_server_price(self):
        result = self._pricing(plan_id=str(self.plan.pk), tier_id=str(self.tier.pk))
        self.assertEqual(result["amount"], Decimal("49.00"))
        self.assertEqual(result["currency"], "GHS")
        self.assertEqual(result["pricing_plan"], self.plan)
        self.assertEqual(result["pricing_tier"], self.tier)

    def test_invoice_checkout_resolves_server_price(self):
        result = self._pricing(invoice_id=str(self.invoice.pk))
        self.assertEqual(result["amount"], Decimal("99.00"))
        self.assertEqual(result["currency"], "GHS")
        self.assertEqual(result["invoice"], self.invoice)

    def test_rejects_lower_client_amount(self):
        with self.assertRaises(CheckoutPricingError):
            self._pricing(plan_id=str(self.plan.pk), tier_id=str(self.tier.pk), posted_amount="1.00")

    def test_rejects_higher_client_amount(self):
        with self.assertRaises(CheckoutPricingError):
            self._pricing(plan_id=str(self.plan.pk), tier_id=str(self.tier.pk), posted_amount="999.00")

    def test_rejects_zero_client_amount(self):
        with self.assertRaises(CheckoutPricingError):
            self._pricing(plan_id=str(self.plan.pk), tier_id=str(self.tier.pk), posted_amount="0")

    def test_rejects_negative_client_amount(self):
        with self.assertRaises(CheckoutPricingError):
            self._pricing(plan_id=str(self.plan.pk), tier_id=str(self.tier.pk), posted_amount="-5.00")

    def test_rejects_precision_manipulation(self):
        with self.assertRaises(CheckoutPricingError):
            self._pricing(plan_id=str(self.plan.pk), tier_id=str(self.tier.pk), posted_amount="48.50")

    def test_rejects_unknown_plan(self):
        with self.assertRaises(CheckoutPricingError):
            self._pricing(plan_id="00000000-0000-0000-0000-000000000999")

    def test_rejects_tier_from_other_plan(self):
        other_plan = PricingPlan.objects.create(
            product=self.product,
            name="Pro",
            slug="pro",
            is_published=True,
        )
        foreign_tier = other_plan.tiers.create(currency="GHS", region="global", amount=Decimal("10.00"))
        with self.assertRaises(CheckoutPricingError):
            self._pricing(plan_id=str(self.plan.pk), tier_id=str(foreign_tier.pk))

    def test_rejects_other_users_invoice(self):
        foreign_invoice = Invoice.objects.create(
            user=self.other,
            invoice_number="INV-2002",
            amount=Decimal("10.00"),
            currency="GHS",
            status=InvoiceStatus.OPEN,
            issued_at="2026-01-01",
            due_at="2026-01-31",
        )
        with self.assertRaises(CheckoutPricingError):
            self._pricing(invoice_id=str(foreign_invoice.pk))

    def test_rejects_currency_mismatch(self):
        with self.assertRaises(CheckoutPricingError):
            self._pricing(plan_id=str(self.plan.pk), tier_id=str(self.tier.pk), posted_currency="USD")

    def test_rejects_missing_selection(self):
        with self.assertRaises(CheckoutPricingError):
            self._pricing()


class CheckoutViewSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer@example.com",
            email="buyer@example.com",
            password="SecurePass123!",
        )
        get_or_create_security_profile(self.user).mark_email_verified()
        self.client.login(username="buyer@example.com", password="SecurePass123!")

        category = ProductCategory.objects.create(name="Vertical", slug="vertical")
        self.product = Product.objects.create(
            name="ChurchHub",
            slug="churchhub",
            category=category,
            is_published=True,
            status=ProductStatus.GA,
        )
        self.plan = PricingPlan.objects.create(
            product=self.product,
            name="Starter",
            slug="starter",
            is_published=True,
        )
        self.tier = self.plan.tiers.create(currency="GHS", region="global", amount=Decimal("49.00"))
        GatewayConfiguration.objects.create(code=MANUAL, name="Manual", is_active=True, is_default=True)

        self.other = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="SecurePass123!",
        )
        self.invoice = Invoice.objects.create(
            user=self.user,
            invoice_number="INV-1001",
            amount=Decimal("99.00"),
            currency="GHS",
            status=InvoiceStatus.OPEN,
            issued_at="2026-01-01",
            due_at="2026-01-31",
        )
        self.foreign_invoice = Invoice.objects.create(
            user=self.other,
            invoice_number="INV-2002",
            amount=Decimal("10.00"),
            currency="GHS",
            status=InvoiceStatus.OPEN,
            issued_at="2026-01-01",
            due_at="2026-01-31",
        )

    def _checkout_post(self, **extra):
        data = {
            "manual_method": "bank_transfer",
            "bank_name": "Test Bank",
            "transfer_reference": "TRX-123",
        }
        data.update(extra)
        if "proof_document" not in data and data.get("manual_method"):
            data["proof_document"] = SimpleUploadedFile(
                "proof.pdf", b"%PDF-1.4 proof", content_type="application/pdf"
            )
        return self.client.post(reverse("payments:checkout"), data)

    def test_normal_checkout_succeeds_with_server_price(self):
        response = self._checkout_post(plan_id=str(self.plan.pk), tier_id=str(self.tier.pk))
        self.assertEqual(response.status_code, 302)
        payment = Payment.objects.get(user=self.user)
        self.assertEqual(payment.amount, Decimal("49.00"))
        self.assertEqual(payment.currency, "GHS")
        self.assertEqual(payment.status, PaymentStatus.PENDING_CONFIRMATION)

    def test_tampered_lower_amount_is_rejected(self):
        response = self._checkout_post(
            plan_id=str(self.plan.pk),
            tier_id=str(self.tier.pk),
            amount="1.00",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Payment.objects.filter(user=self.user).exists())

    def test_checkout_without_plan_or_invoice_is_rejected(self):
        response = self._checkout_post(amount="10.00", currency="GHS")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Payment.objects.filter(user=self.user).exists())

    def test_view_rejects_other_users_invoice(self):
        response = self._checkout_post(invoice_id=str(self.foreign_invoice.pk))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Payment.objects.filter(user=self.user).exists())

    def test_view_rejects_tampered_invoice_amount(self):
        response = self._checkout_post(
            invoice_id=str(self.invoice.pk),
            amount="1.00",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Payment.objects.filter(user=self.user).exists())

    def test_view_rejects_tampered_invoice_currency(self):
        response = self._checkout_post(
            invoice_id=str(self.invoice.pk),
            currency="USD",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Payment.objects.filter(user=self.user).exists())
