from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from accounts.services.email import get_or_create_security_profile
from common.navigation import CONTROL_ROOM_NAV
from products.models import Product, ProductCategory


class ControlRoomViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="control-staff",
            email="control-staff@example.com",
            password="testpass123",
            is_staff=True,
        )
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

    def _assert_staff_page_ok(self, url_name, url_kwargs=None):
        url = reverse(url_name, kwargs=url_kwargs or {})
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            msg=f"{url_name} ({url}) returned HTTP {response.status_code}",
        )

    def test_control_room_nav_pages_load(self):
        skip = {"control_room:team", "control_room:platform_ops"}  # requires platform owner/admin role
        for item in CONTROL_ROOM_NAV:
            if item.get("section") or item.get("external"):
                continue
            if item["url_name"] in skip:
                continue
            self._assert_staff_page_ok(item["url_name"])

    def test_dashboard_shows_cedi_revenue(self):
        response = self.client.get(reverse("control_room:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Revenue (30d)")
        self.assertContains(response, "GH\u20b50")
        self.assertNotContains(response, "$0")

    def test_product_detail_loads(self):
        self._assert_staff_page_ok("control_room:product_detail", {"pk": self.product.pk})

    def test_product_pricing_loads(self):
        self._assert_staff_page_ok("control_room:product_pricing", {"pk": self.product.pk})

    def test_product_create_form_loads(self):
        self._assert_staff_page_ok("control_room:product_create")

    def test_product_edit_form_loads(self):
        self._assert_staff_page_ok("control_room:product_edit", {"pk": self.product.pk})

    def test_brand_kit_loads(self):
        self._assert_staff_page_ok("control_room:brand_kit")

    def test_documentation_hub_loads(self):
        self._assert_staff_page_ok("control_room:documentation")

    def test_documentation_lists_load(self):
        for url_name in (
            "control_room:doc_articles",
            "control_room:doc_videos",
            "control_room:doc_downloads",
            "control_room:doc_categories",
        ):
            self._assert_staff_page_ok(url_name)

    def test_documentation_create_forms_load(self):
        for url_name in (
            "control_room:doc_article_create",
            "control_room:doc_video_create",
            "control_room:doc_download_create",
            "control_room:doc_category_create",
        ):
            self._assert_staff_page_ok(url_name)
