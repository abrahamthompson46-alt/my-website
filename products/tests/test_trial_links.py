from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from common.services.trial_provisioning import DEFAULT_TRIAL_DAYS, provision_trial
from products.models import PricingPlan, Product, ProductCategory
from products.services.trial_links import get_product_trial_url
from django.contrib.auth import get_user_model

User = get_user_model()


class ProductTrialLinkTests(TestCase):
    def setUp(self):
        category = ProductCategory.objects.create(name="Platform", slug="platform")
        self.product = Product.objects.create(
            name="ChurchHub",
            slug="churchhub",
            category=category,
            is_published=True,
            status="ga",
        )
        self.plan = PricingPlan.objects.create(
            product=self.product,
            name="Starter",
            slug="starter",
            is_published=True,
        )
        self.plan.tiers.create(currency="USD", region="global", amount=Decimal("49.00"))

    def test_trial_url_points_to_plan_start(self):
        url = get_product_trial_url(self.product)
        self.assertIn("/products/churchhub/start/", url)
        self.assertIn("plan=starter", url)
        self.assertIn("action=trial", url)

    def test_trial_url_falls_back_to_pricing_without_plan(self):
        product = Product.objects.create(
            name="Empty",
            slug="empty",
            category=self.product.category,
            is_published=True,
            status="ga",
        )
        url = get_product_trial_url(product)
        self.assertEqual(url, reverse("products:pricing", kwargs={"slug": "empty"}))

    def test_trial_url_empty_when_not_purchasable(self):
        product = Product.objects.create(
            name="Soon",
            slug="soon",
            category=self.product.category,
            is_published=True,
            status="coming_soon",
        )
        PricingPlan.objects.create(
            product=product,
            name="Soon Plan",
            slug="soon-plan",
            is_published=True,
        )
        self.assertEqual(get_product_trial_url(product), "")

    def test_provision_trial_uses_thirty_day_default(self):
        user = User.objects.create_user(
            username="trial-user",
            email="trial-user@example.com",
            password="testpass123",
        )
        sub = provision_trial(user=user, product=self.product, plan=self.plan)
        self.assertEqual((sub.trial_ends_at - sub.started_at).days, DEFAULT_TRIAL_DAYS)
        self.assertEqual(DEFAULT_TRIAL_DAYS, 30)
