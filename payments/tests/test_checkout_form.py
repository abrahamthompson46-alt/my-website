from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.services.email import get_or_create_security_profile
from accounts.services.rbac import assign_role
from customer_portal.models.notification import PortalNotification
from payments.constants import MANUAL
from payments.forms import CheckoutForm
from payments.models import GatewayConfiguration, ManualPaymentMethod, Payment, PaymentStatus
from products.models import PricingPlan, Product, ProductCategory, ProductStatus

User = get_user_model()


def _proof_file(name="proof.pdf", content=b"%PDF-1.4 proof"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


class CheckoutFormValidationTests(TestCase):
    def test_online_checkout_does_not_require_manual_fields(self):
        form = CheckoutForm({"manual_method": ""})
        self.assertTrue(form.is_valid())

    def test_bank_transfer_requires_bank_details_and_proof(self):
        form = CheckoutForm(
            {"manual_method": ManualPaymentMethod.BANK_TRANSFER},
            {"proof_document": _proof_file()},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("bank_name", form.errors)
        self.assertIn("transfer_reference", form.errors)

        form = CheckoutForm(
            {
                "manual_method": ManualPaymentMethod.BANK_TRANSFER,
                "bank_name": "Test Bank",
                "transfer_reference": "TRX-123",
            },
            {"proof_document": _proof_file()},
        )
        self.assertTrue(form.is_valid())

    def test_cheque_requires_cheque_number_and_proof(self):
        form = CheckoutForm(
            {"manual_method": ManualPaymentMethod.CHEQUE},
            {"proof_document": _proof_file()},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("cheque_number", form.errors)

        form = CheckoutForm(
            {
                "manual_method": ManualPaymentMethod.CHEQUE,
                "cheque_number": "CHQ-001",
            },
            {"proof_document": _proof_file()},
        )
        self.assertTrue(form.is_valid())

    def test_cash_requires_receipt_number_and_proof(self):
        form = CheckoutForm(
            {"manual_method": ManualPaymentMethod.CASH},
            {"proof_document": _proof_file()},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("receipt_number", form.errors)

        form = CheckoutForm(
            {
                "manual_method": ManualPaymentMethod.CASH,
                "receipt_number": "RCPT-001",
            },
            {"proof_document": _proof_file()},
        )
        self.assertTrue(form.is_valid())

    def test_manual_method_requires_proof_document(self):
        form = CheckoutForm(
            {
                "manual_method": ManualPaymentMethod.BANK_TRANSFER,
                "bank_name": "Test Bank",
                "transfer_reference": "TRX-123",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("proof_document", form.errors)

    def test_rejects_invalid_proof_extension(self):
        bad_file = SimpleUploadedFile("proof.exe", b"bad", content_type="application/octet-stream")
        form = CheckoutForm(
            {
                "manual_method": ManualPaymentMethod.CASH,
                "receipt_number": "RCPT-001",
            },
            {"proof_document": bad_file},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("proof_document", form.errors)


class CheckoutViewManualValidationTests(TestCase):
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

    def test_manual_checkout_without_proof_is_rejected(self):
        response = self.client.post(
            reverse("payments:checkout"),
            {
                "manual_method": "bank_transfer",
                "bank_name": "Test Bank",
                "transfer_reference": "TRX-123",
                "plan_id": str(self.plan.pk),
                "tier_id": str(self.tier.pk),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Payment.objects.filter(user=self.user).exists())

    def test_manual_checkout_with_proof_succeeds(self):
        response = self.client.post(
            reverse("payments:checkout"),
            {
                "manual_method": "bank_transfer",
                "bank_name": "Test Bank",
                "transfer_reference": "TRX-123",
                "plan_id": str(self.plan.pk),
                "tier_id": str(self.tier.pk),
                "proof_document": _proof_file(),
            },
        )
        self.assertEqual(response.status_code, 302)
        payment = Payment.objects.get(user=self.user)
        self.assertEqual(payment.status, PaymentStatus.PENDING_CONFIRMATION)
        self.assertTrue(payment.manual_detail.proof_document)


class OwnerNotificationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="SecurePass123!",
            is_staff=True,
        )
        owner_role = Role.objects.create(name="Platform Owner", slug="platform-owner")
        assign_role(self.owner, owner_role)
        owner_profile = get_or_create_security_profile(self.owner)
        owner_profile.email_verified = True
        owner_profile.mfa_enabled = True
        owner_profile.save(update_fields=["email_verified", "mfa_enabled"])
        self.buyer = User.objects.create_user(
            username="buyer@example.com",
            email="buyer@example.com",
            password="SecurePass123!",
        )
        GatewayConfiguration.objects.create(code=MANUAL, name="Manual", is_active=True, is_default=True)
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

    def test_payment_notifies_platform_owner(self):
        from payments.services.checkout import create_checkout

        create_checkout(
            user=self.buyer,
            amount=Decimal("49.00"),
            currency="GHS",
            gateway_code=MANUAL,
            pricing_plan=self.plan,
            pricing_tier=self.tier,
            manual_method="bank_transfer",
            manual_detail={
                "bank_name": "Test Bank",
                "transfer_reference": "TRX-123",
                "proof_document": _proof_file(),
            },
        )
        notification = PortalNotification.objects.get(user=self.owner)
        self.assertIn("Manual payment", notification.title)
        self.assertEqual(notification.link_url, reverse("operations:payments"))

    def test_demo_request_notifies_platform_owner(self):
        from common.services.demo_requests import log_demo_submission
        from products.models import ProductDemoRequest

        demo = ProductDemoRequest.objects.create(
            full_name="Jane Doe",
            work_email="jane@example.com",
            company="Acme",
            source="homepage",
        )
        log_demo_submission(None, demo)
        notification = PortalNotification.objects.get(user=self.owner)
        self.assertIn("demo request", notification.title.lower())
        self.assertEqual(notification.link_url, reverse("operations:demo_requests"))

    def test_notification_read_redirects_to_link(self):
        notification = PortalNotification.objects.create(
            user=self.owner,
            title="Test",
            message="Click through",
            link_url=reverse("operations:payments"),
        )
        self.client.login(username="owner@example.com", password="SecurePass123!")
        response = self.client.get(
            reverse("customer_portal:notification_read", kwargs={"pk": notification.pk})
        )
        self.assertRedirects(response, reverse("operations:payments"))
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
