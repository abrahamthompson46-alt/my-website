from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from control_room.forms import PlatformSettingsForm
from control_room.models import PlatformSettings


class BrandUploadFormTests(TestCase):
    def setUp(self):
        self.settings = PlatformSettings.load()

    def _form_data(self):
        return {
            field.name: field.value_from_object(self.settings)
            for field in PlatformSettings._meta.fields
            if field.name not in {"id", "created_at", "updated_at", "singleton_key", "brand_logo", "brand_favicon"}
        }

    def test_accepts_svg_favicon(self):
        svg = SimpleUploadedFile(
            "favicon.svg",
            b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" fill="#2563eb"/></svg>',
            content_type="image/svg+xml",
        )
        form = PlatformSettingsForm(
            data=self._form_data(),
            files={"brand_favicon": svg},
            instance=self.settings,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_accepts_svg_logo(self):
        svg = SimpleUploadedFile(
            "logo.svg",
            b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" fill="#2563eb"/></svg>',
            content_type="image/svg+xml",
        )
        form = PlatformSettingsForm(
            data=self._form_data(),
            files={"brand_logo": svg},
            instance=self.settings,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_invalid_extension(self):
        bad = SimpleUploadedFile("favicon.txt", b"not an image", content_type="text/plain")
        form = PlatformSettingsForm(
            data=self._form_data(),
            files={"brand_favicon": bad},
            instance=self.settings,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("brand_favicon", form.errors)
