from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from io import BytesIO
from unittest import mock

from PIL import Image

from accounts.models import Role, User
from accounts.services.email import get_or_create_security_profile
from accounts.services.rbac import assign_role
from products.models import Product, ProductCategory
from products.models.media import ProductScreenshot


def _png_upload(name="dashboard.png"):
    buffer = BytesIO()
    Image.new("RGB", (32, 32), color=(30, 58, 95)).save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


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
            name="CoreTrust",
            slug="microfinance-core",
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

    def test_screenshot_upload_succeeds(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                url = reverse(
                    "control_room:product_screenshot_create",
                    kwargs={"product_pk": self.product.pk},
                )
                response = self.client.post(
                    url,
                    {
                        "title": "Dashboard",
                        "alt_text": "CoreTrust dashboard overview",
                        "image": _png_upload(),
                        "caption": "",
                        "kind": "screenshot",
                        "sort_order": 1,
                    },
                )
                self.assertEqual(response.status_code, 302)
                self.assertEqual(ProductScreenshot.objects.filter(product=self.product).count(), 1)

    def test_screenshot_upload_surfaces_storage_errors(self):
        url = reverse(
            "control_room:product_screenshot_create",
            kwargs={"product_pk": self.product.pk},
        )
        with mock.patch(
            "products.models.media.ProductScreenshot.save",
            side_effect=PermissionError("Permission denied"),
        ):
            response = self.client.post(
                url,
                {
                    "title": "Dashboard",
                    "alt_text": "CoreTrust dashboard overview",
                    "image": _png_upload("fail.png"),
                    "caption": "",
                    "kind": "screenshot",
                    "sort_order": 1,
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Could not save the file on the server")
        self.assertEqual(ProductScreenshot.objects.count(), 0)
