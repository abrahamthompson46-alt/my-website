from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from customer_portal.models import License, Subscription
from customer_portal.models.license import LicenseStatus
from customer_portal.models.subscription import BillingInterval, SubscriptionStatus
from customer_portal.services import get_launchable_subscriptions
from accounts.services.email import get_or_create_security_profile
from organizations.services import ACTIVE_ORG_SESSION_KEY, ensure_default_organization
from products.models import Product, ProductCategory, ProductStatus

User = get_user_model()


class LaunchableSubscriptionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="launcher@example.com",
            email="launcher@example.com",
            password="SecurePass123!",
        )
        get_or_create_security_profile(self.user).mark_email_verified()
        self.org = ensure_default_organization(self.user, company="Launch Org")
        self.category = ProductCategory.objects.create(name="Vertical", slug="vertical-launch")
        self.churchhub = Product.objects.create(
            name="ChurchHub",
            slug="churchhub-launch",
            category=self.category,
            status=ProductStatus.GA,
            is_published=True,
            external_app_url="https://mychurch.zreta.com/",
        )
        self.coretrust = Product.objects.create(
            name="CoreTrust",
            slug="coretrust-launch",
            category=self.category,
            status=ProductStatus.GA,
            is_published=True,
            external_app_url="https://micro.zreta.com/",
        )
        self.no_url = Product.objects.create(
            name="ERP Suite",
            slug="erp-launch",
            category=self.category,
            status=ProductStatus.GA,
            is_published=True,
        )

    def _login(self):
        self.client.force_login(self.user)
        session = self.client.session
        session[ACTIVE_ORG_SESSION_KEY] = str(self.org.pk)
        session.save()

    def _sub(self, product, *, status=SubscriptionStatus.ACTIVE, org=None):
        return Subscription.objects.create(
            user=self.user,
            product=product,
            plan_name="Starter",
            status=status,
            billing_interval=BillingInterval.MONTHLY,
            amount=Decimal("49.00"),
            currency="USD",
            started_at=timezone.now().date(),
            renews_at=timezone.now().date() + timedelta(days=30),
            organization=org or self.org,
        )

    def test_returns_unique_products_with_external_urls(self):
        self._sub(self.churchhub)
        self._sub(self.churchhub, status=SubscriptionStatus.TRIAL)
        self._sub(self.coretrust)
        self._sub(self.no_url)

        launchable = get_launchable_subscriptions(self.user, organization=self.org)
        urls = [sub.product.external_app_url for sub in launchable]
        self.assertEqual(len(launchable), 2)
        self.assertIn("https://mychurch.zreta.com/", urls)
        self.assertIn("https://micro.zreta.com/", urls)

    def test_excludes_expired_subscriptions(self):
        self._sub(self.churchhub, status=SubscriptionStatus.EXPIRED)
        self.assertEqual(
            get_launchable_subscriptions(self.user, organization=self.org),
            [],
        )

    def test_dashboard_shows_launch_actions(self):
        self._sub(self.coretrust)
        self._login()
        response = self.client.get(reverse("customer_portal:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Launch CoreTrust")
        self.assertContains(response, "https://micro.zreta.com/")

    def test_subscriptions_page_shows_launch_button(self):
        self._sub(self.churchhub)
        self._login()
        response = self.client.get(reverse("customer_portal:subscriptions"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Launch app")
        self.assertContains(response, "https://mychurch.zreta.com/")
