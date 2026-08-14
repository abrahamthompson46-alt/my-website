"""RBAC regression tests for control room destructive/configuration views."""

from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User
from accounts.services.email import get_or_create_security_profile
from accounts.services.rbac import assign_role
from products.models import Product, ProductCategory


class ControlRoomRBACTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="pass",
            is_staff=True,
        )
        self.staff = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="pass",
            is_staff=True,
        )
        owner_role = Role.objects.create(name="Platform Owner", slug="platform-owner")
        assign_role(self.owner, owner_role)
        for user in (self.owner, self.staff):
            profile = get_or_create_security_profile(user)
            profile.email_verified = True
            profile.mfa_enabled = True
            profile.save(update_fields=["email_verified", "mfa_enabled"])

        category = ProductCategory.objects.create(name="Platform", slug="platform")
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            category=category,
            is_published=True,
        )

    def test_staff_can_view_dashboard(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("control_room:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_open_settings(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("control_room:settings"))
        self.assertEqual(response.status_code, 403)

    def test_owner_can_open_settings(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("control_room:settings"))
        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_create_product(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("control_room:product_create"))
        self.assertEqual(response.status_code, 403)

    def test_owner_can_create_product_form(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("control_room:product_create"))
        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_run_seed(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("control_room:seed_run", kwargs={"key": "cms"}))
        self.assertEqual(response.status_code, 403)

    def test_owner_can_run_seed(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("control_room:seed_run", kwargs={"key": "cms"}))
        self.assertNotEqual(response.status_code, 403)

    def test_staff_can_view_product_detail(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("control_room:product_detail", kwargs={"pk": self.product.pk}))
        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_edit_product(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("control_room:product_edit", kwargs={"pk": self.product.pk}))
        self.assertEqual(response.status_code, 403)
