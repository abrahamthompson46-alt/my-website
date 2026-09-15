from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from core.services.sanitize import run_sanitization
from customer_portal.models import License, Subscription
from customer_portal.models.license import LicenseStatus
from customer_portal.models.subscription import BillingInterval, SubscriptionStatus
from organizations.services import ensure_default_organization
from payments.constants import MANUAL
from payments.models import GatewayConfiguration, Payment, PaymentStatus
from payments.services.billing_sync import sync_payment_success
from products.models import PricingPlan, Product, ProductCategory, ProductStatus

User = get_user_model()


class BillingSyncOrganizationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="payer@example.com",
            email="payer@example.com",
            password="SecurePass123!",
        )
        self.org = ensure_default_organization(self.user, company="Payer Org")
        self.category = ProductCategory.objects.create(
            name="Vertical", slug="vertical-sanitize"
        )
        self.product = Product.objects.create(
            name="ChurchHub",
            slug="churchhub-sanitize",
            category=self.category,
            status=ProductStatus.GA,
            is_published=True,
        )
        self.plan = PricingPlan.objects.create(
            product=self.product,
            name="Starter",
            slug="starter-sanitize",
            billing_interval="monthly",
            is_published=True,
        )
        self.gateway = GatewayConfiguration.objects.create(
            name="Manual",
            code=MANUAL,
            is_active=True,
            is_default=True,
        )

    def test_successful_plan_payment_creates_org_scoped_subscription(self):
        payment = Payment.objects.create(
            user=self.user,
            gateway=self.gateway,
            reference="PAY-SANITIZE-1",
            amount=Decimal("49.00"),
            currency="USD",
            status=PaymentStatus.SUCCEEDED,
            pricing_plan=self.plan,
            organization=self.org,
            paid_at=timezone.now(),
        )

        subscription = sync_payment_success(payment)

        self.assertEqual(subscription.organization_id, self.org.id)
        self.assertEqual(subscription.status, SubscriptionStatus.ACTIVE)
        license_obj = License.objects.get(subscription=subscription)
        self.assertEqual(license_obj.organization_id, self.org.id)


class SanitizePlatformTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="sanitize@example.com",
            email="sanitize@example.com",
            password="SecurePass123!",
        )
        self.org = ensure_default_organization(self.user)
        self.category = ProductCategory.objects.create(
            name="Vertical", slug="vertical-sanitize-2"
        )
        self.product = Product.objects.create(
            name="Microfinance Core",
            slug="microfinance-core",
            category=self.category,
            status=ProductStatus.COMING_SOON,
            is_published=True,
            is_featured=True,
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            product=self.product,
            plan_name="Growth",
            status=SubscriptionStatus.TRIAL,
            billing_interval=BillingInterval.MONTHLY,
            amount=Decimal("0.00"),
            currency="USD",
            started_at=timezone.now().date() - timedelta(days=40),
            trial_ends_at=timezone.now().date() - timedelta(days=1),
            organization=None,
        )

    def test_dry_run_reports_issues_without_fixing(self):
        report = run_sanitization(fix=False)
        codes = {f.code: f for f in report.findings}
        self.assertGreaterEqual(codes["null_organization"].count, 1)
        self.assertGreaterEqual(codes["featured_policy"].count, 1)
        self.assertGreaterEqual(codes["coretrust_catalog"].count, 1)
        self.assertEqual(report.fixed_total, 0)
        self.subscription.refresh_from_db()
        self.assertIsNone(self.subscription.organization_id)
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_featured)
        self.assertEqual(self.product.name, "Microfinance Core")

    def test_fix_repairs_safe_issues(self):
        report = run_sanitization(fix=True)
        self.assertGreater(report.fixed_total, 0)

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.organization_id, self.org.id)
        self.assertEqual(self.subscription.status, SubscriptionStatus.EXPIRED)

        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "CoreTrust")
        self.assertFalse(self.product.is_featured)
        self.assertEqual(self.product.status, ProductStatus.GA)
        self.assertTrue(self.product.external_app_url)

    def test_management_command_dry_run(self):
        call_command("sanitize_platform")
