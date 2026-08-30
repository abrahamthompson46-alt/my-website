from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User
from accounts.services.email import get_or_create_security_profile
from accounts.services.rbac import assign_role
from products.models import PricingPlan, Product, ProductCategory


class ProductMediaViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="testpass123",
            is_staff=True,
        )
        owner_role = Role.objects.create(name="Platform Owner", slug="platform-owner")
        assign_role(self.user, owner_role)
        profile = get_or_create_security_profile(self.user)
        profile.email_verified = True
        profile.mfa_enabled = True
        profile.save(update_fields=["email_verified", "mfa_enabled"])
        self.client.force_login(self.user)

        category = ProductCategory.objects.create(name="Platform", slug="platform")
        self.product = Product.objects.create(
            name="ChurchHub",
            slug="churchhub",
            category=category,
            is_published=True,
        )

    def test_screenshot_manager_loads_for_platform_owner(self):
        url = reverse("control_room:product_screenshots", kwargs={"product_pk": self.product.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_template_manager_loads_for_platform_owner(self):
        url = (
            reverse("control_room:product_screenshots", kwargs={"product_pk": self.product.pk})
            + "?kind=template"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_video_manager_loads_for_platform_owner(self):
        url = reverse("control_room:product_videos", kwargs={"product_pk": self.product.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_screenshot_create_form_loads(self):
        url = reverse("control_room:product_screenshot_create", kwargs={"product_pk": self.product.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
