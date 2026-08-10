from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from common.services.trial_provisioning import provision_trial
from customer_portal.models import License, Subscription
from customer_portal.models.subscription import SubscriptionStatus
from products.models import PricingPlan, Product

User = get_user_model()


class TrialProvisioningTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer1",
            email="buyer1@example.com",
            password="test-pass-123",
        )
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            tagline="Test",
            short_description="Test",
            is_published=True,
        )
        self.plan = PricingPlan.objects.create(
            product=self.product,
            name="Starter",
            slug="starter",
            is_published=True,
        )
        self.plan.tiers.create(currency="USD", region="global", amount=Decimal("49.00"))

    def test_provision_trial_creates_subscription_and_license(self):
        sub = provision_trial(user=self.user, product=self.product, plan=self.plan)
        self.assertEqual(sub.status, SubscriptionStatus.TRIAL)
        self.assertIsNotNone(sub.trial_ends_at)
        self.assertTrue(License.objects.filter(user=self.user, product=self.product).exists())
        self.assertEqual(Subscription.objects.filter(user=self.user).count(), 1)
